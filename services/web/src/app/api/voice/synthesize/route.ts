import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";

const TTS_SERVICE_URL = process.env.TTS_SERVICE_URL || "http://localhost:8002";

/**
 * POST /api/voice/synthesize - Convert text to speech using ElevenLabs
 */
export async function POST(request: NextRequest) {
  try {
    // Validate session
    const session = await auth.api.getSession({
      headers: request.headers,
    });

    if (!session) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { text, languageCode } = await request.json(); // Default to Bella voice

    if (!text) {
      return NextResponse.json({ error: "Text is required" }, { status: 400 });
    }

		if (!languageCode) {
			return NextResponse.json({ error: "Language is required" });
		}

    if (text.length > 5000) {
      return NextResponse.json(
        { error: "Text too long (max 5000 characters)" },
        { status: 400 }
      );
    }

		const ttsResponse = await fetch(`${TTS_SERVICE_URL}/generate`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({
				text,
				"language_code": languageCode
			})
		})

    if (!ttsResponse.ok) {
	    throw new Error(`TTS server responded with status ${ttsResponse.status}`);
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
