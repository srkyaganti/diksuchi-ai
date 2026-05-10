import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";

const VOICE_SERVICE_URL = process.env.VOICE_SERVICE_URL || "http://localhost:8000";

// Keep in sync with services/voice-service/tts/registry.py LANGUAGE_ENGINE.
const SUPPORTED_TTS_LANGUAGES = new Set([
  "as", "bn", "brx", "hne", "doi", "en", "gu", "hi", "kn", "ml",
  "mni", "mr", "ne", "or", "pa", "sa", "ta", "te",
  "he",
]);
const TTS_LANGUAGE_ALIASES: Record<string, string> = { iw: "he" };

function normalizeLanguageCode(code: string): string {
  const lower = code.trim().toLowerCase();
  return TTS_LANGUAGE_ALIASES[lower] ?? lower;
}

/**
 * POST /api/voice/synthesize - Convert text to speech via voice-service.
 */
export async function POST(request: NextRequest) {
  try {
    const session = await auth.api.getSession({
      headers: request.headers,
    });

    if (!session) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { text, languageCode } = await request.json();

    if (!text) {
      return NextResponse.json({ error: "Text is required" }, { status: 400 });
    }

    if (!languageCode) {
      return NextResponse.json(
        { error: "Language is required" },
        { status: 400 }
      );
    }

    const normalized = normalizeLanguageCode(languageCode);
    if (!SUPPORTED_TTS_LANGUAGES.has(normalized)) {
      return NextResponse.json(
        {
          error: "unsupported_language",
          language_code: languageCode,
          supported: Array.from(SUPPORTED_TTS_LANGUAGES).sort(),
        },
        { status: 400 }
      );
    }

    if (text.length > 5000) {
      return NextResponse.json(
        { error: "Text too long (max 5000 characters)" },
        { status: 400 }
      );
    }

		const ttsResponse = await fetch(`${VOICE_SERVICE_URL}/tts/generate`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({
				text,
				"language_code": normalized
			})
		})

    if (!ttsResponse.ok) {
	    throw new Error(`Voice service TTS responded with status ${ttsResponse.status}`);
    }

    // Get the audio buffer from the FastAPI response
    const audioBuffer = await ttsResponse.arrayBuffer();

    // Return the audio response with appropriate headers
    return new NextResponse(audioBuffer, {
      headers: {
        "Content-Type": "audio/wav",
        "Content-Disposition": "attachment; filename=output.wav",
        "Cache-Control": "no-cache",
      },
    });
  } catch (error) {
    console.error("Text-to-speech error:", error);
    const errorMessage =
      error instanceof Error ? error.message : "Text-to-speech failed";
    return NextResponse.json({ error: errorMessage }, { status: 500 });
  }
}
