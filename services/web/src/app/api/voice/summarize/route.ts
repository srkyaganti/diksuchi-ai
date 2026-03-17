import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { createOpenAICompatible } from "@ai-sdk/openai-compatible";
import { generateText } from "ai";

const SUMMARIZE_PROMPT = `You are preparing text for voice transcription. Your task is to convert the input text into clear, natural-sounding sentences suitable for text-to-speech.

RULES:
1. Break down complex content into short to medium-length sentences (15-25 words each)
2. For TABLES: Describe them naturally. Example: "The table shows 3 rows comparing X, Y, and Z values. Row 1 shows..."
3. For CODE BLOCKS: Summarize what the code does. Example: "Here's a code example that demonstrates how to..."
4. For IMAGES/FIGURES: Describe what they show. Example: "The diagram illustrates..."
5. For BULLET POINTS: Convert to natural sentences. Example: "There are three main points. First,... Second,..."
6. For HEADERS: Just read them as transitions. Example: "Moving to the section about..."
7. Remove all markdown formatting (bold, italic, links, etc.)
8. Maintain factual accuracy - do not add or remove information
9. Keep technical terms and proper nouns
10. Add natural pauses by splitting long sentences

OUTPUT FORMAT:
Return ONLY a JSON array of sentences. Each sentence should end with proper punctuation.
Example: ["First sentence.", "Second sentence.", "Third sentence."]

IMPORTANT: Return ONLY valid JSON array, no other text.`;

const LLM_TIMEOUT_MS = 120_000;

export async function POST(request: NextRequest) {
  const requestId = crypto.randomUUID().slice(0, 8);
  const startTime = Date.now();

  try {
    const session = await auth.api.getSession({
      headers: request.headers,
    });

    if (!session) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    let text: string | undefined;
    let languageCode: string | undefined;

    try {
      const body = await request.json();
      text = body.text;
      languageCode = body.languageCode;
    } catch (parseErr) {
      console.error(`[${requestId}] [SUMMARIZE] Failed to parse body:`, parseErr);
      return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
    }

    if (!text) {
      return NextResponse.json({ error: "Text is required" }, { status: 400 });
    }

    if (text.length > 10000) {
      return NextResponse.json(
        { error: "Text too long (max 10000 characters)" },
        { status: 400 }
      );
    }

    const llmServiceUrl = process.env.LLM_SERVICE_BASE_URL || "http://localhost:11434/v1";
    const modelName = process.env.LLM_MODEL || "llama3.2:3b";

    const llmService = createOpenAICompatible({
      name: "llm-service",
      baseURL: llmServiceUrl,
    });

    console.log(`[${requestId}] [SUMMARIZE] text=${text.length} chars, lang=${languageCode}, model=${modelName}`);
    const llmStartTime = Date.now();

    const { text: responseText } = await generateText({
      model: llmService(modelName),
      system: SUMMARIZE_PROMPT,
      prompt: text,
      temperature: 0.3,
      abortSignal: AbortSignal.timeout(LLM_TIMEOUT_MS),
    });

    const llmDuration = Date.now() - llmStartTime;
    console.log(`[${requestId}] [SUMMARIZE] LLM completed in ${llmDuration}ms, response=${responseText?.length} chars`);

    let sentences: string[];
    try {
      const cleanedResponse = responseText
        .replace(/```json\n?/g, "")
        .replace(/```\n?/g, "")
        .trim();
      sentences = JSON.parse(cleanedResponse);

      if (!Array.isArray(sentences)) {
        throw new Error("Response is not an array");
      }

      sentences = sentences
        .filter((s) => typeof s === "string" && s.trim().length > 0)
        .map((s) => s.trim());
    } catch (parseError) {
      console.warn(`[${requestId}] [SUMMARIZE] JSON parse failed, falling back to sentence splitting`);
      sentences = responseText
        .split(/(?<=[.!?])\s+/)
        .map((s) => s.trim())
        .filter((s) => s.length > 0);
    }

    if (sentences.length === 0) {
      sentences = [text.substring(0, 200)];
    }

    const totalDuration = Date.now() - startTime;
    console.log(`[${requestId}] [SUMMARIZE] Done in ${totalDuration}ms, ${sentences.length} sentences`);

    return NextResponse.json({
      sentences,
      originalLength: text.length,
      summarizedLength: sentences.join(" ").length,
      sentenceCount: sentences.length,
    });
  } catch (error) {
    const totalDuration = Date.now() - startTime;
    console.error(`[${requestId}] [SUMMARIZE] Error after ${totalDuration}ms:`, error);
    const errorMessage =
      error instanceof Error ? error.message : "Summarization failed";
    return NextResponse.json({ error: errorMessage }, { status: 500 });
  }
}
