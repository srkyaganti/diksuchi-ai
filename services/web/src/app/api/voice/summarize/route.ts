import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { createOpenAICompatible } from "@ai-sdk/openai-compatible";
import { generateText } from "ai";
import { languageName, IDENTIFIER_PRESERVATION_RULES } from "@/lib/languages";

// Hard cap any single sentence we return to the synthesizer. Indic Parler /
// HebTTS quality degrades on long inputs, so we split anything over this.
const MAX_SENTENCE_CHARS = 180;
const LLM_TIMEOUT_MS = 120_000;

function buildSummarizePrompt(languageCode: string | undefined): string {
  const langName = languageName(languageCode);
  return `You are preparing text for voice synthesis (text-to-speech). Convert the input into clear, natural-sounding sentences ready to be spoken aloud.

LANGUAGE (STRICT):
- ALL output sentences MUST be in **${langName}**.
- If the input is in a different language, TRANSLATE it into ${langName} while preserving meaning.
- Do NOT mix languages in a single sentence except for the identifiers listed in the IDENTIFIERS section below.

${IDENTIFIER_PRESERVATION_RULES}

LENGTH (STRICT):
- Target 8-15 words per sentence.
- Hard maximum: 20 words OR 180 characters, whichever comes first.
- If a thought needs more, split it into multiple sentences.

CONTENT RULES:
1. Tables → describe naturally, e.g. "The table compares three values across rows."
2. Code blocks → summarize what they do; do not read code verbatim.
3. Images/figures → describe what they show.
4. Bullet points → flowing sentences ("First… Second… Third…").
5. Headers → read as short transitions.
6. Remove all markdown formatting (bold, italic, links, headings).
7. Preserve factual content; do not add or omit information.

OUTPUT FORMAT:
Return ONLY a valid JSON array of sentence strings, each ending with proper punctuation. No other text, no code fences, no commentary.
Example: ["First sentence.", "Second sentence.", "Third sentence."]

/no_think`;
}

// Splits any sentence longer than MAX_SENTENCE_CHARS into smaller pieces,
// first preferring internal-clause boundaries, then falling back to word
// boundaries so the synthesizer never receives an overlong chunk.
function ensureMaxSentenceLength(sentences: string[]): string[] {
  const out: string[] = [];

  const hardSplitByWords = (s: string): string[] => {
    const words = s.split(/\s+/).filter(Boolean);
    const chunks: string[] = [];
    let cur = "";
    for (const w of words) {
      const candidate = cur ? `${cur} ${w}` : w;
      if (candidate.length > MAX_SENTENCE_CHARS && cur) {
        chunks.push(cur);
        cur = w;
      } else {
        cur = candidate;
      }
    }
    if (cur) chunks.push(cur);
    return chunks;
  };

  for (const sentence of sentences) {
    if (sentence.length <= MAX_SENTENCE_CHARS) {
      out.push(sentence);
      continue;
    }
    // Pass 1: greedy pack on internal-clause boundaries
    const clauses = sentence.split(/(?<=[,;:—–])\s+/);
    let buf = "";
    const merged: string[] = [];
    for (const c of clauses) {
      const candidate = buf ? `${buf} ${c}` : c;
      if (candidate.length <= MAX_SENTENCE_CHARS) {
        buf = candidate;
      } else {
        if (buf) merged.push(buf);
        buf = c;
      }
    }
    if (buf) merged.push(buf);

    // Pass 2: any clause still over the cap gets word-split
    for (const m of merged) {
      if (m.length <= MAX_SENTENCE_CHARS) out.push(m);
      else out.push(...hardSplitByWords(m));
    }
  }
  return out;
}

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
      system: buildSummarizePrompt(languageCode),
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
      sentences = [text.substring(0, MAX_SENTENCE_CHARS)];
    }

    // Safety net: even with the prompt's length rule, small LLMs sometimes
    // emit overlong sentences. Split anything still over the cap.
    const beforeSplit = sentences.length;
    sentences = ensureMaxSentenceLength(sentences);
    if (sentences.length !== beforeSplit) {
      console.log(
        `[${requestId}] [SUMMARIZE] length-cap split: ${beforeSplit} → ${sentences.length} sentences`,
      );
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
