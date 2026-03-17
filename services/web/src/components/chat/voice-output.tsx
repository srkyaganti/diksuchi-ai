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
const MAX_CACHE_SIZE = 5;
const MAX_SUMMARIZE_CACHE = 10;

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

  // Ref mirrors for stable event handler access
  const currentIndexRef = useRef(0);
  const languageCodeRef = useRef(languageCode);
  const playNextSentenceRef = useRef<() => void>(() => {});
  const stopPlaybackRef = useRef<() => void>(() => {});
  const isStartingPlaybackRef = useRef(false);

  // Summarize result cache to avoid re-calling LLM for same text
  const summarizeCacheRef = useRef<Map<string, string[]>>(new Map());

  // Keep refs in sync with state/props
  useEffect(() => {
    currentIndexRef.current = currentIndex;
  }, [currentIndex]);

  useEffect(() => {
    languageCodeRef.current = languageCode;
  }, [languageCode]);

  const revokeAllUrls = useCallback(() => {
    audioCacheRef.current.forEach((url) => {
      URL.revokeObjectURL(url);
    });
    audioCacheRef.current.clear();
  }, []);

  const cleanupOldCache = useCallback((forIndex: number) => {
    if (audioCacheRef.current.size <= MAX_CACHE_SIZE) return;

    const keysToDelete: number[] = [];
    audioCacheRef.current.forEach((_, key) => {
      if (key < forIndex - 1) {
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
  }, []);

  // Memoized with no deps -- reads languageCode from ref
  const synthesizeSentence = useCallback(
    async (
      sentence: string,
      index: number,
      signal: AbortSignal
    ): Promise<string | null> => {
      if (audioCacheRef.current.has(index)) {
        return audioCacheRef.current.get(index)!;
      }

      if (prefetchInProgressRef.current.has(index)) {
        // Wait for in-progress prefetch to complete
        return new Promise((resolve) => {
          const check = () => {
            if (audioCacheRef.current.has(index)) {
              resolve(audioCacheRef.current.get(index)!);
            } else if (!prefetchInProgressRef.current.has(index)) {
              resolve(null); // Prefetch finished but failed
            } else {
              setTimeout(check, 50);
            }
          };
          check();
        });
      }

      prefetchInProgressRef.current.add(index);

      try {
        const response = await fetch("/api/voice/synthesize", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            text: sentence,
            languageCode: languageCodeRef.current,
          }),
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
    },
    [cleanupOldCache]
  );

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
    [synthesizeSentence]
  );

  // Reads currentIndex from ref to avoid stale closure
  const playNextSentence = useCallback(() => {
    const current = currentIndexRef.current;
    const nextIndex = current + 1;
    const sentences = sentencesRef.current;

    if (nextIndex >= sentences.length) {
      setIsPlaying(false);
      currentIndexRef.current = 0;
      setCurrentIndex(0);
      setTotalSentences(0);
      sentencesRef.current = [];
      return;
    }

    currentIndexRef.current = nextIndex;
    setCurrentIndex(nextIndex);

    const audioUrl = audioCacheRef.current.get(nextIndex);

    if (audioUrl && audioRef.current) {
      audioRef.current.src = audioUrl;
      audioRef.current.play().catch(console.error);
      prefetchSentences(nextIndex + 1);
    } else if (abortControllerRef.current) {
      // Audio not cached yet -- synthesize on demand then play
      synthesizeSentence(
        sentences[nextIndex],
        nextIndex,
        abortControllerRef.current.signal
      ).then((url) => {
        if (url && audioRef.current) {
          audioRef.current.src = url;
          audioRef.current.play().catch(console.error);
          prefetchSentences(nextIndex + 1);
        } else {
          setIsPlaying(false);
          toast.error("Failed to play next sentence");
        }
      });
    } else {
      setIsPlaying(false);
      toast.error("Failed to play next sentence");
    }
  }, [prefetchSentences, synthesizeSentence]);

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
    currentIndexRef.current = 0;
    setCurrentIndex(0);
    setTotalSentences(0);
    setIsPlaying(false);
    setIsLoading(false);
    setIsSummarizing(false);
    prefetchInProgressRef.current.clear();
    revokeAllUrls();
  }, [revokeAllUrls]);

  // Keep callback refs in sync
  useEffect(() => {
    playNextSentenceRef.current = playNextSentence;
  }, [playNextSentence]);

  useEffect(() => {
    stopPlaybackRef.current = stopPlayback;
  }, [stopPlayback]);

  // Audio event listeners -- uses refs so handlers always dispatch to latest callbacks
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleEnded = () => {
      playNextSentenceRef.current();
    };
    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    const handleError = () => {
      // Ignore errors during playback startup (e.g., clearing previous audio)
      if (isStartingPlaybackRef.current) return;
      // Ignore errors when not actively playing (cleanup/unmount artifacts)
      if (!abortControllerRef.current) return;
      toast.error("Audio playback error");
      stopPlaybackRef.current();
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
      stopPlaybackRef.current();
      revokeAllUrls();
    };
  }, [revokeAllUrls]);

  const startPlayback = useCallback(async () => {
    if (!text || isStartingPlaybackRef.current) return;

    // Abort any previous playback first
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      // Do NOT set src="" here — it triggers an async error event that
      // would abort the new AbortController created below.
      // The src will be overwritten when the first sentence is ready.
    }
    revokeAllUrls();

    isStartingPlaybackRef.current = true;

    try {
      setIsSummarizing(true);
      abortControllerRef.current = new AbortController();
      const signal = abortControllerRef.current.signal;

      // Check summarize cache first
      const cacheKey = `${text}:${languageCodeRef.current}`;
      let sentences: string[];
      const cachedSentences = summarizeCacheRef.current.get(cacheKey);

      if (cachedSentences) {
        sentences = cachedSentences;
      } else {
        const summarizeResponse = await fetch("/api/voice/summarize", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            text,
            languageCode: languageCodeRef.current,
          }),
          signal,
        });

        if (!summarizeResponse.ok) {
          const error = await summarizeResponse.json().catch(() => ({}));
          throw new Error(error.error || "Failed to summarize text");
        }

        const data: SummarizeResponse = await summarizeResponse.json();
        sentences = data.sentences;

        if (sentences.length === 0) {
          throw new Error("No sentences to speak");
        }

        // Cache the result
        summarizeCacheRef.current.set(cacheKey, sentences);
        if (summarizeCacheRef.current.size > MAX_SUMMARIZE_CACHE) {
          const firstKey = summarizeCacheRef.current.keys().next().value;
          if (firstKey !== undefined) {
            summarizeCacheRef.current.delete(firstKey);
          }
        }
      }

      sentencesRef.current = sentences;
      setTotalSentences(sentences.length);
      currentIndexRef.current = 0;
      setCurrentIndex(0);
      setIsSummarizing(false);
      setIsLoading(true);

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
      isStartingPlaybackRef.current = false;
    }
  }, [text, prefetchSentences, revokeAllUrls]);

  // Auto-play when text changes and not disabled
  useEffect(() => {
    if (autoPlay && text && text !== previousTextRef.current && !isDisabled) {
      previousTextRef.current = text;
      const timer = setTimeout(() => {
        startPlayback();
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [text, autoPlay, isDisabled, startPlayback]);

  // Stop playback when disabled
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
