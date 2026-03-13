import { NextRequest, NextResponse } from "next/server";
import prisma from "@/lib/prisma";
import { auth } from "@/lib/auth";
import { streamText, convertToModelMessages } from "ai";
import { createOpenAICompatible } from "@ai-sdk/openai-compatible";
import { loadCollectionDocuments } from "@/lib/document-loader";
import type { DocumentContent } from "@/lib/document-loader";
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
 * Build system prompt from full document content (long-context approach).
 * Includes resolvable image URLs so the LLM can produce valid markdown images.
 */
function buildSystemPrompt(documents: DocumentContent[]): string {
  if (documents.length === 0) {
    return `You are a helpful technical assistant. No documents have been processed for this collection yet.`;
  }

  const documentSections = documents.map((doc, i) => {
    let section = `=== DOCUMENT ${i + 1}: ${doc.fileName} ===\n\n${doc.textContent}`;

    if (doc.imageRefs.length > 0) {
      const imageList = doc.imageRefs
        .map((ref) => {
          const url = `/api/files/${doc.fileId}/images/${ref.filename}`;
          let entry = `- ${ref.filename} (URL: ${url})`;
          if (ref.caption) entry += ` -- ${ref.caption}`;
          if (ref.page) entry += ` (page ${ref.page})`;
          return entry;
        })
        .join("\n");
      section += `\n\nAvailable images in this document:\n${imageList}`;
    }

    return section;
  });

  return `You are a technical assistant with access to the following documents from the knowledge base. These are safety-critical technical manuals -- pay special attention to any warnings, cautions, or safety information.

${documentSections.join("\n\n")}

Answer the user's question accurately based on the documents above. If the information is not sufficient, say so.

When referencing an image, use markdown image syntax with the full URL path provided above. For example: ![Description](/api/files/FILEID/images/picture_1.png)`;
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

    // Load full document content from Docling JSON (long-context approach)
    const documents = await loadCollectionDocuments(collectionId);
    const systemPrompt = buildSystemPrompt(documents);

    const fileNames = documents.map((d) => d.fileName);

    await prisma.chatMessage.create({
      data: {
        sessionId: session.id,
        role: "user",
        content: queryText,
      },
    });

    const modelMessages = convertToModelMessages(messages);

    const result = streamText({
      model: llmService(modelName),
      system: systemPrompt,
      messages: modelMessages,
      temperature: 0.0,
      onFinish: async ({ text }) => {
        try {
          await prisma.chatMessage.create({
            data: {
              sessionId: session!.id,
              role: "assistant",
              content: text,
              sources: fileNames,
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
