import { NextRequest, NextResponse } from "next/server";
import prisma from "@/lib/prisma";
import { auth } from "@/lib/auth";
import { getActiveOrganizationId } from "@/lib/org-context";
import {
  streamText,
  convertToModelMessages,
  createUIMessageStream,
  createUIMessageStreamResponse,
} from "ai";
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
function buildSystemPrompt(
  sections: SectionResult[],
  uuidToFileId: Record<string, string> = {},
): string {
  if (sections.length === 0) {
    return `You are a senior technical publications specialist with deep expertise in defence equipment documentation following S1000D standards. Your users are defence personnel — technicians, engineers, and officers — who rely on your answers to perform actual maintenance, repair, troubleshooting, and operational tasks on equipment.

No relevant sections were found in the knowledge base for this query.

INSTRUCTIONS:
1. Clearly state that no matching documentation was found for the query.
2. Suggest how the user might refine their question (e.g. different terminology, broader/narrower scope, specific equipment name or part number).
3. Do NOT guess, fabricate, or provide information from general knowledge. Only information from the retrieved documentation is trustworthy for defence equipment work.`;
  }

  const sectionBlocks = sections.map((sec, i) => {
    return `=== SECTION ${i + 1}: ${sec.sectionPath} ===\n\n${sec.content}`;
  });

  // Collect resolved image URLs with captions across all sections
  const imageRefs: string[] = [];
  const seenImages = new Set<string>();
  for (const sec of sections) {
    const fileId = uuidToFileId[sec.documentUuid];
    if (!fileId || !sec.images) continue;
    for (const img of sec.images) {
      const key = `${fileId}/${img}`;
      if (seenImages.has(key)) continue;
      seenImages.add(key);
      const caption = sec.imageCaptions?.[img] || img;
      imageRefs.push(
        `- ![${caption}](/api/files/${fileId}/images/${img}) — ${caption} (from **${sec.sectionPath}**)`,
      );
    }
  }

  let prompt = `You are a senior technical publications specialist with deep expertise in defence equipment documentation following S1000D standards. Your users are defence personnel — technicians, engineers, and officers — who rely on your answers to perform actual maintenance, repair, troubleshooting, and operational tasks on equipment. Your responses must be detailed enough to directly guide hands-on work.

RETRIEVED DOCUMENTATION:
The following sections have been retrieved from the S1000D knowledge base. This is your ONLY source of truth.

${sectionBlocks.join("\n\n")}

---

RESPONSE RULES (follow in order of priority):

## 1. SAFETY FIRST
- All WARNINGS, CAUTIONS, and NOTES from the source material MUST be included in your response. Never omit them.
- Place each warning or caution BEFORE the step or information it applies to, not after. A technician must read the warning before performing the action.
- Format safety information prominently:
  - **WARNING:** (risk of injury or death)
  - **CAUTION:** (risk of equipment damage)
  - **NOTE:** (important supplementary information)

## 2. COMPLETENESS — DO NOT SUMMARIZE
- Your users perform real work based on your answers. Provide COMPLETE, VERBOSE, DETAILED responses.
- Include every relevant detail from the source sections: all steps, all specifications, all conditions, all notes.
- Do NOT shorten, abbreviate, paraphrase, or omit steps. Reproduce procedural content fully.
- If a procedure has 20 steps, list all 20 steps. If a description spans multiple paragraphs, include the full description.
- When specifications are provided (torque values, pressures, tolerances, fluid capacities, part numbers, NSNs), reproduce them EXACTLY as written — do not round, convert, or approximate.

## 3. STRUCTURE YOUR RESPONSE BASED ON QUERY TYPE
Detect the nature of the user's question and structure accordingly:

**For procedural questions** (how to repair, replace, install, remove, service, inspect):
- List prerequisites (tools, parts, materials, conditions) if mentioned in the source
- Provide numbered step-by-step instructions in the exact order from the source
- Include all sub-steps
- Note any inspection criteria or acceptance standards
- Include post-procedure checks if documented

**For descriptive questions** (what is, how does it work, describe the system):
- Provide the full technical description from the source
- Include operating principles, component functions, and system relationships
- Include all specifications, parameters, and performance data

**For fault isolation / troubleshooting questions** (what's wrong, why does, diagnose):
- Present symptoms and probable causes as documented
- Provide fault isolation steps in order
- Include test procedures and expected readings
- List corrective actions for each identified fault

## 4. CITATIONS AND TRACEABILITY
- Reference the section path when presenting information (e.g. "According to **[Section Path]**...").
- When information comes from multiple sections, cite each one where relevant.
- This allows the user to locate and verify the original source material.

## 5. ACCURACY — NEVER FABRICATE
- Answer based ONLY on the retrieved sections above. This is non-negotiable.
- NEVER invent part numbers, NSNs, torque values, specifications, procedures, or any technical data.
- If the retrieved sections contain only partial information, provide what is available and explicitly state what is missing (e.g. "The source documentation does not specify the torque value for this fastener.").
- If the retrieved information is insufficient to answer the question, say so clearly and suggest what documentation the user might need.

## 6. LANGUAGE
- Respond in the same language the user writes in.
- Use clear, direct technical language. Prefer active voice.
- Use standard technical terminology consistent with the source material.`;

  if (imageRefs.length > 0) {
    prompt += `

## 7. IMAGES AND FIGURES
The following images were extracted from the source documents with descriptions of their content. Include them in your response ONLY where they are relevant to the user's question. Use the exact markdown image syntax provided.

${imageRefs.join("\n")}

When including an image, use the provided description to introduce it naturally (e.g. "The following figure shows the disc brake assembly:"). Place images inline within your response near the relevant step or description, not grouped at the end.`;
  }

  return prompt;
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
    const activeOrgId = await getActiveOrganizationId(authSession);

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
      collection.organizationId !== activeOrgId
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
        session.organizationId !== activeOrgId
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

    // Resolve document UUIDs to file IDs for image URL construction
    const docUuids = [...new Set(sections.map((s) => s.documentUuid))];
    const uuidToFileId: Record<string, string> = {};
    if (docUuids.length > 0) {
      const files = await prisma.file.findMany({
        where: { uuid: { in: docUuids } },
        select: { id: true, uuid: true },
      });
      for (const f of files) uuidToFileId[f.uuid] = f.id;
    }

    const systemPrompt = buildSystemPrompt(sections, uuidToFileId);

    // Build structured source references with page numbers
    const sources = sections.map((s) => ({
      fileId: uuidToFileId[s.documentUuid] || null,
      fileName: "",
      sectionPath: s.sectionPath,
      pageNo: s.pageNo || null,
      documentUuid: s.documentUuid,
    }));

    // Resolve file names for source references
    const allFileIds = sources
      .map((s) => s.fileId)
      .filter(Boolean) as string[];
    if (allFileIds.length > 0) {
      const fileRecords = await prisma.file.findMany({
        where: { id: { in: allFileIds } },
        select: { id: true, name: true },
      });
      const fileIdToName = Object.fromEntries(
        fileRecords.map((f) => [f.id, f.name]),
      );
      for (const src of sources) {
        if (src.fileId) {
          src.fileName = fileIdToName[src.fileId] || "";
        }
      }
    }

    const sectionPaths = sections.map((s) => s.sectionPath);

    const userParts = lastMessage.parts || [{ type: "text" as const, text: queryText }];

    console.log(`Saving user message to session ${session.id}`);
    await prisma.chatMessage.create({
      data: {
        sessionId: session.id,
        role: "user",
        content: queryText,
        parts: JSON.parse(JSON.stringify(userParts)),
      },
    });

    // Strip document-image file parts from history before converting to model
    // messages — they are UI-only references (/api/files/…) that the LLM
    // provider cannot resolve and would cause the stream to error.
    const cleanedMessages: UIMessage[] = messages.map((msg) => {
      if (msg.role !== "assistant" || !msg.parts) return msg;
      return {
        ...msg,
        parts: msg.parts.filter(
          (p) => p.type !== "file",
        ),
      };
    });
    const modelMessages = convertToModelMessages(cleanedMessages);

    // Collect unique document images to stream as file parts
    const imageParts: Array<{
      type: "file";
      url: string;
      mediaType: string;
      filename: string;
    }> = [];
    const seenImages = new Set<string>();
    for (const section of sections) {
      const fileId = uuidToFileId[section.documentUuid];
      if (!fileId || !section.images) continue;
      for (const imgFile of section.images) {
        const key = `${fileId}/${imgFile}`;
        if (seenImages.has(key)) continue;
        seenImages.add(key);
        imageParts.push({
          type: "file",
          url: `/api/files/${fileId}/images/${imgFile}`,
          mediaType: "image/png",
          filename: imgFile,
        });
      }
    }

    const stream = createUIMessageStream({
      generateId: () => nanoid(),
      execute: async ({ writer }) => {
        // Write document images as file parts before text
        // Note: stream chunk schema is strict — only { type, url, mediaType } allowed
        for (const imgPart of imageParts) {
          writer.write({
            type: imgPart.type,
            url: imgPart.url,
            mediaType: imgPart.mediaType,
          });
        }

        // Stream LLM response and merge into the same message
        const result = streamText({
          model: llmService(modelName),
          system: systemPrompt,
          messages: modelMessages,
          temperature: 0.0,
          onFinish: async ({ text, toolCalls, toolResults }) => {
            if (!session?.id) {
              console.error(
                "Cannot save assistant message: session ID is missing",
              );
              return;
            }

            try {
              const parts: any[] = [];

              // Persist image parts
              for (const imgPart of imageParts) {
                parts.push(imgPart);
              }

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
                  sessionId: session.id,
                  role: "assistant",
                  content: text,
                  parts:
                    parts.length > 0
                      ? JSON.parse(JSON.stringify(parts))
                      : undefined,
                  sources: sources.length > 0 ? sources : undefined,
                },
              });
              console.log(`Saved assistant message to session ${session.id}`);
            } catch (error) {
              console.error("Failed to save assistant message:", error);
            }
          },
        });

        writer.merge(result.toUIMessageStream());
      },
      onError: (error) => {
        console.error("Stream error:", error);
        if (error == null) return "An unknown error occurred";
        if (typeof error === "string") return error;
        if (error instanceof Error) return error.message;
        return JSON.stringify(error);
      },
    });

    return createUIMessageStreamResponse({ stream });
  } catch (error) {
    console.error("Chat API error:", error);
    const errorMessage =
      error instanceof Error ? error.message : "Internal server error";
    return NextResponse.json({ error: errorMessage }, { status: 500 });
  }
}
