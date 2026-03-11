import { NextRequest, NextResponse } from 'next/server';
import { auth } from "@/lib/auth";

const VOICE_SERVICE_URL = process.env.VOICE_SERVICE_URL || "http://localhost:8000";

/**
 * POST /api/voice/transcribe - Transcribe audio using local Whisper server
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

    const formData = await request.formData();
    const audioBlob = formData.get("audio") as Blob;

    if (!audioBlob) {
      return NextResponse.json({ error: "No audio provided" }, { status: 400 });
    }

    // Prepare FormData for Whisper server
    const whisperFormData = new FormData();
    // Whisper server expects "file" field with WAV audio
    // Audio is already converted to WAV format in the voice-input component
    whisperFormData.append("file", audioBlob, "audio.wav");
    whisperFormData.append("temperature", "0.0");
    whisperFormData.append("response_format", "verbose_json");

    console.log("Sending to Voice Service STT:", {
      url: `${VOICE_SERVICE_URL}/stt/transcribe`,
      blobSize: audioBlob.size,
      blobType: audioBlob.type,
    });

    // Send to Voice Service
    const whisperResponse = await fetch(`${VOICE_SERVICE_URL}/stt/transcribe`, {
      method: "POST",
      body: whisperFormData,
    });

    if (!whisperResponse.ok) {
      const errorText = await whisperResponse.text();
      throw new Error(`Voice service responded with status ${whisperResponse.status}: ${errorText}`);
    }

    const result = await whisperResponse.json();

    // Log full response for debugging
    console.log("Voice Service STT response:", JSON.stringify(result, null, 2));

    // Validate response structure
    if (!result.text) {
      throw new Error(
        "Invalid Voice Service response: missing 'text' field. Response: " +
          JSON.stringify(result)
      );
    }

    // Log detected language for debugging
    console.log(
      "STT Result - Language:",
      result.language || "unknown",
      "Confidence:",
      result.language_probability || 0,
      "Text length:",
      result.text.length
    );

    // Map Voice Service response to match expected format
    // Voice Service returns ISO 639-1 codes (e.g., "hi"), which is what we need
    const detectedLanguage = result.language || result.detected_language || "unknown";
    const languageCode = mapLanguageToCode(detectedLanguage.toLowerCase());

    return NextResponse.json({
      text: result.text,
      languageCode: languageCode,
      confidence: result.language_probability || result.detected_language_probability || 0,
    });
  } catch (error) {
    console.error("Transcription error:", error);
    const errorMessage =
      error instanceof Error ? error.message : "Transcription failed";
    return NextResponse.json(
      {
        error: errorMessage,
        hint: "Make sure Voice Service is running at " + VOICE_SERVICE_URL,
      },
      { status: 500 }
    );
  }
}

/**
 * Map full language name to ISO 639-1 code
 * Whisper returns full names (e.g., "english"), we need codes (e.g., "en")
 */
function mapLanguageToCode(language: string): string {
	const languageMap: Record<string, string> = {
    english: "en",
    spanish: "es",
    french: "fr",
    german: "de",
    italian: "it",
    portuguese: "pt",
    russian: "ru",
    chinese: "zh",
    japanese: "ja",
    korean: "ko",
    hindi: "hi",
    arabic: "ar",
    bengali: "bn",
    tamil: "ta",
    telugu: "te",
    marathi: "mr",
    gujarati: "gu",
    kannada: "kn",
    malayalam: "ml",
    punjabi: "pa",
    // Add more mappings as needed
  };

  const lowerLang = language?.toLowerCase() || "";
  return languageMap[lowerLang] || lowerLang;
}
