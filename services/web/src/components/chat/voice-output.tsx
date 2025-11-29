"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Volume2, Square } from "lucide-react";
import { toast } from "sonner";

interface VoiceOutputProps {
  text: string;
  isDisabled?: boolean;
	languageCode: string;
  autoPlay?: boolean;
}

export function VoiceOutput({ text, languageCode, isDisabled, autoPlay = false }: VoiceOutputProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);
  const previousTextRef = useRef<string>("");
  const audioUrlRef = useRef<string | null>(null);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleEnded = () => setIsPlaying(false);
    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);

    audio.addEventListener("ended", handleEnded);
    audio.addEventListener("play", handlePlay);
    audio.addEventListener("pause", handlePause);

    return () => {
      audio.removeEventListener("ended", handleEnded);
      audio.removeEventListener("play", handlePlay);
      audio.removeEventListener("pause", handlePause);

      // Cleanup: revoke object URL to prevent memory leaks
      if (audioUrlRef.current) {
        URL.revokeObjectURL(audioUrlRef.current);
      }
    };
  }, []);

  // Auto-play when text changes and autoPlay is enabled
  useEffect(() => {
    if (autoPlay && text && text !== previousTextRef.current && !isDisabled) {
      previousTextRef.current = text;
      // Small delay to ensure audio element is ready
      const timer = setTimeout(() => {
        handleSpeak();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [text, autoPlay, isDisabled]);

  const handleSpeak = async () => {
    if (!text) return;

    try {
      setIsLoading(true);

      const response = await fetch("/api/voice/synthesize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, languageCode }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.error || "Failed to synthesize speech");
      }

      // Verify content type is audio
      const contentType = response.headers.get("Content-Type");
      if (!contentType?.includes("audio/wav")) {
        throw new Error("Invalid audio format received");
      }

      // Get the audio blob from the API response
      const audioBlob = await response.blob();

      // Revoke previous URL to prevent memory leaks
      if (audioUrlRef.current) {
        URL.revokeObjectURL(audioUrlRef.current);
      }

      // Create new object URL for the audio blob
      const audioUrl = URL.createObjectURL(audioBlob);
      audioUrlRef.current = audioUrl;

      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        await audioRef.current.play();
      }
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Speech synthesis failed";
      toast.error(message);
      setIsPlaying(false);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStop = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
    }
  };

  // Auto-play mode - show minimal controls (stop button only when playing/loading)
  if (autoPlay) {
    return (
      <div className="flex gap-2 items-center">
        {(isPlaying || isLoading) && (
          <Button
            onClick={handleStop}
            size="sm"
            variant="ghost"
            className={isPlaying ? "animate-pulse" : ""}
            title={isLoading ? "Stop preparing audio" : "Stop audio playback"}
          >
            <Square className="w-4 h-4" />
            {isLoading ? "Cancel" : "Stop"}
          </Button>
        )}
        <audio ref={audioRef} className="hidden" />
      </div>
    );
  }

  // Manual play mode - show full controls
  return (
    <div className="flex gap-2 items-center">
      {!isPlaying ? (
        <Button
          onClick={handleSpeak}
          disabled={isDisabled || isLoading || !text}
          size="sm"
          variant="ghost"
        >
          <Volume2 className="w-4 h-4" />
          {isLoading ? "Preparing..." : "Speak"}
        </Button>
      ) : (
        <Button
          onClick={handleStop}
          size="sm"
          variant="ghost"
          className="animate-pulse"
        >
          <Square className="w-4 h-4" />
          Stop
        </Button>
      )}
      <audio ref={audioRef} className="hidden" />
    </div>
  );
}
