"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Volume2, Square, Loader2 } from "lucide-react";
import { toast } from "sonner";

interface VoiceOutputProps {
  text: string;
  isDisabled?: boolean;
  languageCode: string;
  autoPlay?: boolean;
}

interface SummarizeResponse {
  sentences: string[];
  originalLength: number;
  summarizedLength: number;
  sentenceCount: number;
}

const PREFETCH_COUNT = 3;
const SENTENCE_GAP_MS = 400;
const MAX_CACHE_SIZE = 5;

export function VoiceOutput({
  text,
  languageCode,
  isDisabled,
  autoPlay = false,
}: VoiceOutputProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSummarizing, setIsSummarizing] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [totalSentences, setTotalSentences] = useState(0);

  const audioRef = useRef<HTMLAudioElement>(null);
  const previousTextRef = useRef<string>("");
  const sentencesRef = useRef<string[]>([]);
  const audioCacheRef = useRef<Map<number, string>>(new Map());
  const abortControllerRef = useRef<AbortController | null>(null);
  const prefetchInProgressRef = useRef<Set<number>>(new Set());

  const revokeAllUrls = useCallback(() => {
    audioCacheRef.current.forEach((url) => {
      URL.revokeObjectURL(url);
    });
    audioCacheRef.current.clear();
  }, []);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleEnded = () => {
      playNextSentence();
    };
    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    const handleError = () => {
      toast.error("Audio playback error");
      stopPlayback();
    };

    audio.addEventListener("ended", handleEnded);
    audio.addEventListener("play", handlePlay);
    audio.addEventListener("pause", handlePause);
    audio.addEventListener("error", handleError);

    return () => {
      audio.removeEventListener("ended", handleEnded);
      audio.removeEventListener("play", handlePlay);
      audio.removeEventListener("pause", handlePause);
      audio.removeEventListener("error", handleError);
      stopPlayback();
      revokeAllUrls();
    };
  }, [revokeAllUrls]);

  const synthesizeSentence = async (
    sentence: string,
    index: number,
    signal: AbortSignal
  ): Promise<string | null> => {
    if (audioCacheRef.current.has(index)) {
      return audioCacheRef.current.get(index)!;
    }

    if (prefetchInProgressRef.current.has(index)) {
      return null;
    }

    prefetchInProgressRef.current.add(index);

    try {
      const response = await fetch("/api/voice/synthesize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: sentence, languageCode }),
        signal,
      });

      if (!response.ok) {
        throw new Error("Failed to synthesize");
      }

      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);

      cleanupOldCache(index);
      audioCacheRef.current.set(index, audioUrl);

      return audioUrl;
    } catch (error) {
      if ((error as Error).name === "AbortError") {
        return null;
      }
      console.error(`Failed to synthesize sentence ${index}:`, error);
      return null;
    } finally {
      prefetchInProgressRef.current.delete(index);
    }
  };

  const cleanupOldCache = (currentIndex: number) => {
    if (audioCacheRef.current.size <= MAX_CACHE_SIZE) return;

    const keysToDelete: number[] = [];
    audioCacheRef.current.forEach((_, key) => {
      if (key < currentIndex - 1) {
        keysToDelete.push(key);
      }
    });

    keysToDelete.forEach((key) => {
      const url = audioCacheRef.current.get(key);
      if (url) {
        URL.revokeObjectURL(url);
        audioCacheRef.current.delete(key);
      }
    });
  };

  const prefetchSentences = useCallback(
    async (fromIndex: number) => {
      if (!abortControllerRef.current) return;

      const sentences = sentencesRef.current;
      const signal = abortControllerRef.current.signal;

      const prefetchPromises: Promise<void>[] = [];

      for (let i = 0; i < PREFETCH_COUNT; i++) {
        const index = fromIndex + i;
        if (index < sentences.length && !audioCacheRef.current.has(index)) {
          prefetchPromises.push(
            synthesizeSentence(sentences[index], index, signal).then(() => {})
          );
        }
      }

      await Promise.allSettled(prefetchPromises);
    },
    []
  );

  const playNextSentence = useCallback(() => {
    const nextIndex = currentIndex + 1;
    const sentences = sentencesRef.current;

    if (nextIndex >= sentences.length) {
      setIsPlaying(false);
      setCurrentIndex(0);
      setTotalSentences(0);
      sentencesRef.current = [];
      return;
    }

    setCurrentIndex(nextIndex);
    const audioUrl = audioCacheRef.current.get(nextIndex);

    if (audioUrl && audioRef.current) {
      audioRef.current.src = audioUrl;
      audioRef.current.play().catch(console.error);
      prefetchSentences(nextIndex + 1);
    } else {
      setIsPlaying(false);
      toast.error("Failed to play next sentence");
    }
  }, [currentIndex, prefetchSentences]);

  const startPlayback = async () => {
    if (!text) return;

    try {
      setIsSummarizing(true);
      abortControllerRef.current = new AbortController();

      const summarizeResponse = await fetch("/api/voice/summarize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, languageCode }),
        signal: abortControllerRef.current.signal,
      });

      if (!summarizeResponse.ok) {
        const error = await summarizeResponse.json().catch(() => ({}));
        throw new Error(error.error || "Failed to summarize text");
      }

      const data: SummarizeResponse = await summarizeResponse.json();
      const sentences = data.sentences;

      if (sentences.length === 0) {
        throw new Error("No sentences to speak");
      }

      sentencesRef.current = sentences;
      setTotalSentences(sentences.length);
      setCurrentIndex(0);
      setIsSummarizing(false);
      setIsLoading(true);

      revokeAllUrls();

      await prefetchSentences(0);

      const firstAudioUrl = audioCacheRef.current.get(0);
      if (firstAudioUrl && audioRef.current) {
        audioRef.current.src = firstAudioUrl;
        await audioRef.current.play();
      } else {
        throw new Error("Failed to prepare audio");
      }
    } catch (error) {
      if ((error as Error).name === "AbortError") {
        return;
      }
      const message =
        error instanceof Error ? error.message : "Voice output failed";
      toast.error(message);
      setIsPlaying(false);
    } finally {
      setIsLoading(false);
      setIsSummarizing(false);
    }
  };

  const stopPlayback = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current.src = "";
    }

    sentencesRef.current = [];
    setCurrentIndex(0);
    setTotalSentences(0);
    setIsPlaying(false);
    setIsLoading(false);
    setIsSummarizing(false);
    prefetchInProgressRef.current.clear();
    revokeAllUrls();
  }, [revokeAllUrls]);

  useEffect(() => {
    if (autoPlay && text && text !== previousTextRef.current && !isDisabled) {
      previousTextRef.current = text;
      const timer = setTimeout(() => {
        startPlayback();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [text, autoPlay, isDisabled]);

  useEffect(() => {
    if (isDisabled) {
      stopPlayback();
    }
  }, [isDisabled, stopPlayback]);

  const getStatusText = () => {
    if (isSummarizing) return "Preparing...";
    if (isLoading) return "Loading audio...";
    if (isPlaying && totalSentences > 0) {
      return `${currentIndex + 1}/${totalSentences}`;
    }
    return "";
  };

  if (autoPlay) {
    return (
      <div className="flex gap-2 items-center">
        {(isPlaying || isLoading || isSummarizing) && (
          <>
            <Button
              onClick={stopPlayback}
              size="sm"
              variant="ghost"
              className={isPlaying ? "animate-pulse" : ""}
              title={isSummarizing ? "Cancel preparation" : "Stop audio playback"}
            >
              {isSummarizing || isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Square className="w-4 h-4" />
              )}
              {isSummarizing ? "Cancel" : "Stop"}
            </Button>
            {isPlaying && (
              <span className="text-xs text-muted-foreground">
                {getStatusText()}
              </span>
            )}
          </>
        )}
        <audio ref={audioRef} className="hidden" />
      </div>
    );
  }

  return (
    <div className="flex gap-2 items-center">
      {!isPlaying && !isLoading && !isSummarizing ? (
        <Button
          onClick={startPlayback}
          disabled={isDisabled || !text}
          size="sm"
          variant="ghost"
        >
          <Volume2 className="w-4 h-4" />
          Speak
        </Button>
      ) : (
        <Button onClick={stopPlayback} size="sm" variant="ghost">
          {isSummarizing || isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Square className="w-4 h-4" />
          )}
          {isSummarizing ? "Preparing..." : isLoading ? "Loading..." : "Stop"}
        </Button>
      )}
      {isPlaying && totalSentences > 0 && (
        <span className="text-xs text-muted-foreground">
          {currentIndex + 1}/{totalSentences}
        </span>
      )}
      <audio ref={audioRef} className="hidden" />
    </div>
  );
}
