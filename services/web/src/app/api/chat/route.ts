import { NextRequest, NextResponse } from "next/server";
import prisma from "@/lib/prisma";
import { auth } from "@/lib/auth";
import { streamText, convertToModelMessages } from "ai";
import { createOpenAICompatible } from "@ai-sdk/openai-compatible";
import { retrieveDocuments } from "@/lib/python-client";
import type { SectionResult } from "@/lib/python-client";
import type { UIMessage } from "ai";
import { nanoid } from "nanoid";

export const runtime = "nodejs";
export const maxDuration = 300;

interface ChatRequestBody {
  messages: UIMessage[];
  collectionId: string;
  sessionId?: string;
}

/**
 * Build system prompt from retrieved sections (hybrid RAG approach).
 * Each section is the full parent context around the matched chunks,
 * giving the LLM complete context to avoid hallucination.
 */
function buildSystemPrompt(sections: SectionResult[]): string {
  if (sections.length === 0) {
    return `You are a helpful technical assistant. No relevant sections were found for this query. If you cannot answer from the provided context, say so clearly.`;
  }

  const sectionBlocks = sections.map((sec, i) => {
    return `=== SECTION ${i + 1}: ${sec.sectionPath} ===\n\n${sec.content}`;
  });

  return `You are a technical assistant for defence-sector S1000D documentation. You have access to the following sections retrieved from the knowledge base. These are safety-critical technical manuals -- pay special attention to any warnings, cautions, or safety information.

${sectionBlocks.join("\n\n")}

INSTRUCTIONS:
- Answer the user's question accurately based ONLY on the sections above.
- If the information is not sufficient to answer, say so clearly -- do NOT guess or fabricate information.
- When citing information, reference the section path (e.g. "According to [Section Path]...").
- Preserve any warnings, cautions, or safety notes from the source material.`;
}

function extractTextContent(parts: any[]): string {
  if (!parts || !Array.isArray(parts)) return "";
  return parts
    .filter((part) => part.type === "text")
    .map((part) => part.text)
    .join("\n");
}

export async function POST(request: NextRequest) {
  try {
    const authSession = await auth.api.getSession({
      headers: request.headers,
    });

    if (!authSession) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const llmServiceUrl =
      process.env.LLM_SERVICE_BASE_URL || "http://localhost:11434/v1";
    const modelName = process.env.LLM_MODEL || "llama3.2:3b";

    const llmService = createOpenAICompatible({
      name: "llm-service",
      baseURL: llmServiceUrl,
    });

    const { messages, collectionId, sessionId } =
      (await request.json()) as ChatRequestBody;

    if (!messages || !collectionId) {
      return NextResponse.json(
        { error: "Missing messages or collectionId" },
        { status: 400 },
      );
    }

    const user = authSession.user as any;

    const collection = await prisma.collection.findFirst({
      where: { id: collectionId },
    });

    if (!collection) {
      return NextResponse.json(
        { error: "Collection not found" },
        { status: 404 },
      );
    }

    if (
      !user.isSuperAdmin &&
      collection.organizationId !== authSession.session?.activeOrganizationId
    ) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    const lastMessage = messages[messages.length - 1];
    if (lastMessage.role !== "user") {
      return NextResponse.json(
        { error: "Last message must be from user" },
        { status: 400 },
      );
    }

    let session = null;
    if (sessionId) {
      session = await prisma.chatSession.findUnique({
        where: { id: sessionId },
      });

      if (!session) {
        return NextResponse.json(
          { error: "Chat session not found" },
          { status: 404 },
        );
      }

      if (
        !user.isSuperAdmin &&
        session.organizationId !== authSession.session?.activeOrganizationId
      ) {
        return NextResponse.json({ error: "Forbidden" }, { status: 403 });
      }
    } else {
      const firstUserMessageText = extractTextContent(lastMessage.parts);
      session = await prisma.chatSession.create({
        data: {
          collectionId,
          organizationId: collection.organizationId,
          userId: authSession.user.id,
          title: firstUserMessageText.substring(0, 50) || "New Chat",
        },
      });
    }

    const queryText = extractTextContent(lastMessage.parts);

    if (!queryText.trim()) {
      return NextResponse.json(
        { error: "Message must contain text content" },
        { status: 400 },
      );
    }

    // Hybrid retrieval: vector + BM25 -> rerank -> section expansion
    let sections: SectionResult[] = [];
    try {
      const retrievalResult = await retrieveDocuments({
        query: queryText,
        collectionId,
        topK: 5,
      });
      sections = retrievalResult.sections;
      console.log(
        `Retrieved ${sections.length} sections in ${retrievalResult.timingMs}ms`,
      );
    } catch (err) {
      console.error("Retrieval failed, proceeding with empty context:", err);
    }

    const systemPrompt = buildSystemPrompt(sections);

    const sectionPaths = sections.map((s) => s.sectionPath);

    const userParts = lastMessage.parts || [{ type: "text" as const, text: queryText }];

    await prisma.chatMessage.create({
      data: {
        sessionId: session.id,
        role: "user",
        content: queryText,
        parts: JSON.parse(JSON.stringify(userParts)),
      },
    });

    const modelMessages = convertToModelMessages(messages);

    const result = streamText({
      model: llmService(modelName),
      system: systemPrompt,
      messages: modelMessages,
      temperature: 0.0,
      onFinish: async ({ text, toolCalls, toolResults }) => {
        try {
          const parts: any[] = [];

          if (toolCalls && toolCalls.length > 0) {
            toolCalls.forEach((tc, i) => {
              const tcAny = tc as any;
              parts.push({
                type: `tool-${tc.toolName}` as any,
                input: tcAny.args,
                output: toolResults?.[i],
                state: toolResults?.[i] ? "output-available" : "pending",
              });
            });
          }

          if (text) {
            parts.push({ type: "text", text });
          }

          await prisma.chatMessage.create({
            data: {
              sessionId: session!.id,
              role: "assistant",
              content: text,
              parts: parts.length > 0 ? JSON.parse(JSON.stringify(parts)) : undefined,
              sources: sectionPaths,
            },
          });
        } catch (error) {
          console.error("Failed to save assistant message:", error);
        }
      },
    });

    return result.toUIMessageStreamResponse({
      originalMessages: messages,
      generateMessageId: () => nanoid(),
      onError: (error) => {
        console.error("Stream error:", error);
        if (error == null) return "An unknown error occurred";
        if (typeof error === "string") return error;
        if (error instanceof Error) return error.message;
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
