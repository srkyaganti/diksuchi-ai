import { NextRequest, NextResponse } from 'next/server';
import { auth } from "@/lib/auth";

const STT_SERVICE_URL = process.env.STT_SERVICE_URL || "http://localhost:8080";

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

    console.log("Sending to STT service:", {
      url: `${STT_SERVICE_URL}/inference`,
      blobSize: audioBlob.size,
      blobType: audioBlob.type,
    });

    // Send to STT service
    const whisperResponse = await fetch(`${STT_SERVICE_URL}/inference`, {
      method: "POST",
      body: whisperFormData,
    });

    if (!whisperResponse.ok) {
	    throw new Error(`Whisper server responded with status ${whisperResponse.status}`);
    }

    const result = await whisperResponse.json();

    // Log full response for debugging
    console.log("Whisper server response:", JSON.stringify(result, null, 2));

    // Validate response structure
    if (!result.text) {
      throw new Error(
        "Invalid Whisper response: missing 'text' field. Response: " +
          JSON.stringify(result)
      );
    }

    // Log detected language for debugging
    console.log(
      "Whisper STT Result - Language:",
      result.detected_language || "unknown",
      "Confidence:",
      result.detected_language_probability || 0,
      "Text length:",
      result.text.length
    );

    // Map Whisper response to match ElevenLabs format
    // ElevenLabs uses language_code (e.g., "en"), Whisper uses full name (e.g., "english")
    // whisper.cpp uses "language" field, Python service uses "detected_language"
    // Convert detected_language to ISO 639-1 code
    const detectedLanguage = result.language || result.detected_language || "unknown";
    const languageCode = mapLanguageToCode(
			detectedLanguage.toLowerCase(),
    );

    return NextResponse.json({
      text: `${result.text}. Respond in ${detectedLanguage}`,
      languageCode: languageCode,
      confidence: result.detected_language_probability || 0,
    });
  } catch (error) {
    console.error("Transcription error:", error);
    const errorMessage =
      error instanceof Error ? error.message : "Transcription failed";
    return NextResponse.json(
      {
        error: errorMessage,
        hint: "Make sure STT service is running at " + STT_SERVICE_URL,
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
