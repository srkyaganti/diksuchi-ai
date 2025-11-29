"use client";

import { useState, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Mic, StopCircle } from "lucide-react";
import { toast } from "sonner";

interface OnTranscribedProps {
	text: string;
	languageCode: string;
}

interface VoiceInputProps {
  onTranscribed: (input: OnTranscribedProps) => void;
  isDisabled?: boolean;
}

export function VoiceInput({ onTranscribed, isDisabled }: VoiceInputProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Try to use a compatible audio format
      // Chrome/Firefox support webm, Safari supports mp4
      let mimeType = "audio/webm";
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = "audio/mp4";
      }
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = ""; // Use browser default
      }

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: mimeType || undefined,
      });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const actualMimeType = mediaRecorder.mimeType;
        const audioBlob = new Blob(audioChunksRef.current, {
          type: actualMimeType,
        });

        console.log("Recorded audio:", {
          mimeType: actualMimeType,
          size: audioBlob.size,
        });

        // Send for transcription
        setIsProcessing(true);
        try {
          // Convert to WAV format before sending
          const wavBlob = await convertToWav(audioBlob);
          console.log("Converted to WAV:", {
            size: wavBlob.size,
            type: wavBlob.type,
          });

          const formData = new FormData();
          formData.append("audio", wavBlob);

          const response = await fetch("/api/voice/transcribe", {
            method: "POST",
            body: formData,
          });

          if (!response.ok) {
            throw new Error("Failed to transcribe audio");
          }

          const data = await response.json();
          onTranscribed({ text: data.text, languageCode: data.languageCode });
          toast.success("Audio transcribed successfully");
        } catch (error) {
          const message =
            error instanceof Error ? error.message : "Transcription failed";
          toast.error(message);
        } finally {
          setIsProcessing(false);

          // Clean up
          stream.getTracks().forEach((track) => track.stop());
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      toast.info("Recording started...");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to start recording";
      toast.error(message);
    }
  }, [onTranscribed]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      toast.info("Recording stopped, processing...");
    }
  }, [isRecording]);

  return (
    <div className="flex gap-2">
      {!isRecording ? (
        <Button
          onClick={startRecording}
          disabled={isDisabled || isProcessing}
          size="sm"
          variant="secondary"
        >
          <Mic className="w-4 h-4 mr-2" />
          {isProcessing ? "Processing..." : "Record"}
        </Button>
      ) : (
        <Button
          onClick={stopRecording}
          size="sm"
          variant="destructive"
          className="animate-pulse"
        >
          <StopCircle className="w-4 h-4 mr-2" />
          Stop Recording
        </Button>
      )}
    </div>
  );
}

/**
 * Convert audio blob to WAV format using Web Audio API
 */
async function convertToWav(blob: Blob): Promise<Blob> {
  try {
    // Create audio context
    const audioContext = new AudioContext();

    // Convert blob to array buffer
    const arrayBuffer = await blob.arrayBuffer();

    // Decode audio data
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

    // Convert AudioBuffer to WAV
    const wavBuffer = audioBufferToWav(audioBuffer);

    // Create blob from WAV buffer
    const wavBlob = new Blob([wavBuffer], { type: "audio/wav" });

    return wavBlob;
  } catch (error) {
    console.error("Error converting to WAV:", error);
    throw new Error("Failed to convert audio to WAV format");
  }
}

/**
 * Convert AudioBuffer to WAV format
 */
function audioBufferToWav(audioBuffer: AudioBuffer): ArrayBuffer {
  const numberOfChannels = audioBuffer.numberOfChannels;
  const sampleRate = audioBuffer.sampleRate;
  const format = 1; // PCM
  const bitDepth = 16;

  // Interleave channels
  const length = audioBuffer.length * numberOfChannels * 2;
  const buffer = new ArrayBuffer(44 + length);
  const view = new DataView(buffer);

  // Write WAV header
  const writeString = (offset: number, string: string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  };

  writeString(0, "RIFF");
  view.setUint32(4, 36 + length, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true); // fmt chunk size
  view.setUint16(20, format, true);
  view.setUint16(22, numberOfChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * numberOfChannels * (bitDepth / 8), true);
  view.setUint16(32, numberOfChannels * (bitDepth / 8), true);
  view.setUint16(34, bitDepth, true);
  writeString(36, "data");
  view.setUint32(40, length, true);

  // Write audio data
  const channelData: Float32Array[] = [];
  for (let i = 0; i < numberOfChannels; i++) {
    channelData.push(audioBuffer.getChannelData(i));
  }

  let offset = 44;
  for (let i = 0; i < audioBuffer.length; i++) {
    for (let channel = 0; channel < numberOfChannels; channel++) {
      const sample = Math.max(-1, Math.min(1, channelData[channel][i]));
      view.setInt16(
        offset,
        sample < 0 ? sample * 0x8000 : sample * 0x7fff,
        true
      );
      offset += 2;
    }
  }

  return buffer;
}
