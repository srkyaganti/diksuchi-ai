import { NextRequest, NextResponse } from "next/server";
import prisma from "@/lib/prisma";
import { auth } from "@/lib/auth";
import { streamText, convertToModelMessages } from "ai";
import { createOpenAICompatible } from "@ai-sdk/openai-compatible";
import { pythonClient } from "@/lib/python-client";
import type { UIMessage } from "ai";
import { nanoid } from "nanoid";

export const runtime = "nodejs";
export const maxDuration = 300; // 5 minutes max

interface ChatRequestBody {
  messages: UIMessage[];
  collectionId: string;
  sessionId?: string;
}

/**
 * Build system prompt from retrieval results
 */
function buildSystemPromptFromResults(contextChunks: string[]): string {
  if (contextChunks.length === 0) {
    return `You are a helpful assistant. Answer the user's questions based on your knowledge.`;
  }

  const contextText = contextChunks
    .map((chunk, i) => `[${i + 1}] ${chunk}`)
    .join("\n\n");

  return `You are a helpful assistant with access to the following relevant information from the knowledge base:

${contextText}

Use the provided information to answer the user's question accurately. If the information is not sufficient to answer the question completely, say so. Pay special attention to any warnings or safety information mentioned in the context.`;
}

/**
 * Extract text content from message parts
 */
function extractTextContent(parts: any[]): string {
  if (!parts || !Array.isArray(parts)) {
    return "";
  }

  return parts
    .filter((part) => part.type === "text")
    .map((part) => part.text)
    .join("\n");
}

export async function POST(request: NextRequest) {
  try {
    // Validate session
    const authSession = await auth.api.getSession({
      headers: request.headers,
    });

    if (!authSession) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // Initialize Diksuchi LLM Service provider (OpenAI-compatible)
    const llmServiceUrl = process.env.LLM_SERVICE_BASE_URL || "http://llm-service:8003/v1";
    const modelName = process.env.LLM_MODEL || "llama-3.2-3b-instruct";
    console.log("🤖 LLM Service Configuration:", {
      baseURL: llmServiceUrl,
      model: modelName,
    });

    // Initialize LLM Service provider
    const llmService = createOpenAICompatible({
      name: "llm-service",
      baseURL: llmServiceUrl,
    });

    const { messages, collectionId, sessionId } =
      (await request.json()) as ChatRequestBody;

		console.log(JSON.stringify({
			messages,
			collectionId,
			sessionId,
		}))

    if (!messages || !collectionId) {
      return NextResponse.json(
        { error: "Missing messages or collectionId" },
        { status: 400 }
      );
    }

    const user = authSession.user as any;

    // Verify collection exists and user has permission
    const collection = await prisma.collection.findFirst({
      where: {
        id: collectionId,
      },
    });

    if (!collection) {
      return NextResponse.json(
        { error: "Collection not found" },
        { status: 404 }
      );
    }

    // Check organization access (super admins can access any collection)
    if (
      !user.isSuperAdmin &&
      collection.organizationId !== authSession.session?.activeOrganizationId
    ) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    // Get the last user message
    const lastMessage = messages[messages.length - 1];
    if (lastMessage.role !== "user") {
      return NextResponse.json(
        { error: "Last message must be from user" },
        { status: 400 }
      );
    }

    // Get or create chat session
    let session = null;
    if (sessionId) {
      session = await prisma.chatSession.findUnique({
        where: { id: sessionId },
      });

      if (!session) {
        return NextResponse.json(
          { error: "Chat session not found" },
          { status: 404 }
        );
      }

      // Verify session belongs to user's active organization
      if (
        !user.isSuperAdmin &&
        session.organizationId !== authSession.session?.activeOrganizationId
      ) {
        return NextResponse.json({ error: "Forbidden" }, { status: 403 });
      }
    } else {
      // Create new session
      const firstUserMessageText = extractTextContent(lastMessage.parts);
      session = await prisma.chatSession.create({
        data: {
          collectionId,
          organizationId: collection.organizationId, // From collection
          userId: authSession.user.id, // Creator for audit trail
          title: firstUserMessageText.substring(0, 50) || "New Chat",
        },
      });
    }

    // Extract query text from last message (handles multimodal messages)
    const queryText = extractTextContent(lastMessage.parts);

    if (!queryText.trim()) {
      return NextResponse.json(
        { error: "Message must contain text content" },
        { status: 400 }
      );
    }

    // Build chat history for conversational retrieval
    // Convert UI messages to simple format for Python service
    const chatHistory = messages
      .slice(0, -1) // Exclude the current message
      .map((msg) => ({
        role: msg.role,
        content: extractTextContent(msg.parts),
      }))
      .filter((msg) => msg.content.trim().length > 0); // Filter empty messages

    // Retrieve RAG context using Python conversational retrieval
    const retrievalResponse = await pythonClient.retrieve({
      query: queryText,
      collectionId: collectionId,
      limit: 5,
      rerank: true,
      chatHistory: chatHistory, // Pass conversation history
      useConversationalRetrieval: true, // Enable conversation-aware retrieval
      conversationDepth: 3, // Consider last 3 turns
    });

    // Extract context data for system prompt
    const contextChunks = retrievalResponse.results.map((r) => r.content);
    const fileNames = retrievalResponse.results
      .map((r) => r.fileName)
      .filter((name): name is string => name !== undefined && name !== null);
    const fileIds = retrievalResponse.results
      .map((r) => r.fileId)
      .filter((id): id is string => id !== undefined && id !== null);

    // Build system prompt with hybrid RAG context
    const systemPrompt = buildSystemPromptFromResults(contextChunks);

    // Build system message with RAG context
    const systemMessage = {
      role: "system" as const,
      content: systemPrompt,
    };

    // Save user message to database
    await prisma.chatMessage.create({
      data: {
        sessionId: session.id,
        role: "user",
        content: queryText,
      },
    });

    // Convert UI messages to model messages format
    const modelMessages = convertToModelMessages(messages);

    // Use AI SDK streamText with Diksuchi LLM Service
    const result = streamText({
      model: llmService(modelName),
      system: systemMessage.content,
      messages: modelMessages,
      temperature: 0.0,
      onFinish: async ({ text }) => {
        // Save assistant message to database
        try {
          await prisma.chatMessage.create({
            data: {
              sessionId: session!.id,
              role: "assistant",
              content: text,
              sources: fileNames, // Store source file names from Python retrieval
            },
          });
        } catch (error) {
          console.error("Failed to save assistant message:", error);
        }
      },
    });

    // Return UI message stream with sources injected
    return result.toUIMessageStreamResponse({
      originalMessages: messages,
      generateMessageId: () => nanoid(),
	    // TODO: fix sending sources
      // sendSources: async () => {
      //   // Inject RAG sources as message parts
      //   if (context.chunks.length === 0) {
      //     return [];
      //   }
			//
      //   return context.fileNames.map((name, i) => ({
      //     type: "source-url" as const,
      //     title: name,
      //     url: `/api/files/${context.fileIds[i]}/download`,
      //     snippet: context.chunks[i].substring(0, 200) + "...",
      //     relevance: `${(context.similarities[i] * 100).toFixed(0)}%`,
      //   }));
      // },
      onError: (error) => {
        console.error("Stream error:", error);

        if (error == null) {
          return "An unknown error occurred";
        }

        if (typeof error === "string") {
          return error;
        }

        if (error instanceof Error) {
          return error.message;
        }

        return JSON.stringify(error);
      },
    });
  } catch (error) {
    console.error("Chat API error:", error);
    const errorMessage =
      error instanceof Error ? error.message : "Internal server error";
    return NextResponse.json({ error: errorMessage }, { status: 500 });
  }
}
