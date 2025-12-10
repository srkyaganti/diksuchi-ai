"use client";

import { useState, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Mic, StopCircle, CheckCircle, XCircle, Download } from "lucide-react";
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
  const [isReviewing, setIsReviewing] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const wavBlobRef = useRef<Blob | null>(null);

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

        try {
          // Convert to WAV format before sending
          const wav = await convertToWav(audioBlob);
          console.log("Converted to WAV:", {
            size: wav.size,
            type: wav.type,
          });

          // Store WAV blob and create URL for preview
          wavBlobRef.current = wav;
          const url = URL.createObjectURL(wav);
          setAudioUrl(url);
          setIsReviewing(true);

          // Clean up stream
          stream.getTracks().forEach((track) => track.stop());
        } catch (error) {
          const message =
            error instanceof Error ? error.message : "Failed to process audio";
          toast.error(message);
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

  const approveAndTranscribe = useCallback(async () => {
    if (!wavBlobRef.current) return;

    setIsProcessing(true);
    setIsReviewing(false);
    try {
      const formData = new FormData();
      formData.append("audio", wavBlobRef.current);

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

      // Clean up
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
        setAudioUrl(null);
      }
      wavBlobRef.current = null;
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Transcription failed";
      toast.error(message);
      setIsReviewing(true);
    } finally {
      setIsProcessing(false);
    }
  }, [audioUrl, onTranscribed]);

  const cancelAndRerecord = useCallback(() => {
    setIsReviewing(false);
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
    wavBlobRef.current = null;
    toast.info("Recording cancelled. Click Record to try again.");
  }, [audioUrl]);

  const downloadAudio = useCallback(() => {
    if (!audioUrl) return;

    const a = document.createElement("a");
    a.href = audioUrl;
    a.download = `recording_${new Date().toISOString().slice(0, 19).replace(/:/g, "-")}.wav`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }, [audioUrl]);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex gap-2">
        {!isRecording && !isReviewing ? (
          <Button
            onClick={startRecording}
            disabled={isDisabled || isProcessing}
            size="sm"
            variant="secondary"
          >
            <Mic className="w-4 h-4 mr-2" />
            {isProcessing ? "Processing..." : "Record"}
          </Button>
        ) : isRecording ? (
          <Button
            onClick={stopRecording}
            size="sm"
            variant="destructive"
            className="animate-pulse"
          >
            <StopCircle className="w-4 h-4 mr-2" />
            Stop Recording
          </Button>
        ) : null}
      </div>

      {isReviewing && audioUrl && (
        <div className="flex flex-col gap-2 p-3 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
          <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
            Preview your recording:
          </p>
          <audio
            src={audioUrl}
            controls
            className="w-full h-8"
          />
          <div className="flex gap-2">
            <Button
              onClick={approveAndTranscribe}
              disabled={isProcessing}
              size="sm"
              variant="default"
            >
              <CheckCircle className="w-4 h-4 mr-2" />
              {isProcessing ? "Transcribing..." : "Transcribe"}
            </Button>
            <Button
              onClick={cancelAndRerecord}
              disabled={isProcessing}
              size="sm"
              variant="outline"
            >
              <XCircle className="w-4 h-4 mr-2" />
              Re-record
            </Button>
            <Button
              onClick={downloadAudio}
              disabled={isProcessing}
              size="sm"
              variant="ghost"
              title="Download audio file"
            >
              <Download className="w-4 h-4" />
            </Button>
          </div>
        </div>
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

    // Create and return blob from WAV buffer
    return new Blob([wavBuffer], { type: "audio/wav" });
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
