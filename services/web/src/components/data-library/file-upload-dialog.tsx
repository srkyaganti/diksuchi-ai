"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { IconUpload, IconCheck, IconX } from "@tabler/icons-react";
import { toast } from "sonner";

interface FileUploadDialogProps {
  collectionId: string;
}

type Phase = "idle" | "uploading" | "processing" | "done" | "error";

function uploadFileXHR(
  file: File,
  collectionId: string,
  onProgress: (pct: number) => void
): Promise<{ ok: boolean; status: number; data: any }> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append("file", file);
    formData.append("collectionId", collectionId);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    };

    xhr.onload = () => {
      try {
        resolve({ ok: xhr.status < 400, status: xhr.status, data: JSON.parse(xhr.responseText) });
      } catch {
        reject(new Error("Invalid server response"));
      }
    };

    xhr.onerror = () => reject(new Error("Network error during upload"));
    xhr.open("POST", "/api/files");
    xhr.send(formData);
  });
}

const STEP_LABELS: Record<string, string> = {
  "Starting document processing": "Starting...",
  "Running Docling PDF conversion": "Converting PDF (this takes a while)",
  "Docling conversion complete": "PDF converted",
  "Building section map": "Mapping document structure",
  "Mapping images to sections": "Locating images",
  "Image metadata built": "Images mapped",
  "Saving document to storage": "Saving to storage",
  "Chunking document by sections": "Splitting into searchable chunks",
  "Building BM25 keyword index": "Building keyword index",
  "Document processing completed": "Done!",
};

function friendlyMessage(raw: string | undefined): string {
  if (!raw) return "Processing document...";
  // Pass through per-item messages as-is (they have counts)
  if (raw.startsWith("Captioning image") || raw.startsWith("Embedding chunks")) {
    return raw;
  }
  return STEP_LABELS[raw] ?? raw;
}

export function FileUploadDialog({ collectionId }: FileUploadDialogProps) {
  const [open, setOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingProgress, setProcessingProgress] = useState(0);
  const [processingMessage, setProcessingMessage] = useState("Queued for processing...");
  const [errorMessage, setErrorMessage] = useState("");
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const router = useRouter();

  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  const stopPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  const startPolling = (jobId: string) => {
    pollingRef.current = setInterval(async () => {
      try {
        const res = await fetch(`/api/jobs/${jobId}`);
        if (!res.ok) return;
        const data = await res.json();

        setProcessingProgress(data.progress ?? 0);
        setProcessingMessage(friendlyMessage(data.message));

        if (data.status === "completed") {
          stopPolling();
          setProcessingProgress(100);
          setProcessingMessage("Done!");
          setPhase("done");
          router.refresh();
          setTimeout(() => {
            setOpen(false);
            resetState();
            toast.success("Document ready — chunks embedded and indexed");
          }, 2000);
        } else if (data.status === "failed") {
          stopPolling();
          setPhase("error");
          setErrorMessage(data.error ?? "Processing failed");
          toast.error("Document processing failed");
        }
      } catch {
        // Ignore transient polling errors
      }
    }, 1500);
  };

  const resetState = () => {
    setSelectedFile(null);
    setPhase("idle");
    setUploadProgress(0);
    setProcessingProgress(0);
    setProcessingMessage("Queued for processing...");
    setErrorMessage("");
  };

  const handleOpenChange = (next: boolean) => {
    if (!next) {
      if (phase === "uploading" || phase === "processing") {
        stopPolling();
        resetState();
      }
      if (phase !== "idle") {
        router.refresh();
      }
    }
    setOpen(next);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setSelectedFile(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      toast.error("Please select a file");
      return;
    }

    setPhase("uploading");
    setUploadProgress(0);

    try {
      const result = await uploadFileXHR(selectedFile, collectionId, setUploadProgress);

      if (!result.ok) {
        throw new Error(result.data?.error ?? "Failed to upload file");
      }

      const jobId: string | null = result.data?.jobId ?? null;

      setPhase("processing");
      setProcessingProgress(0);
      setProcessingMessage("Queued for processing...");

      if (jobId) {
        startPolling(jobId);
      } else {
        // Worker unavailable — show static processing state, close after a moment
        toast.success("File uploaded — processing will begin when worker is available");
        setTimeout(() => {
          setOpen(false);
          resetState();
          router.refresh();
        }, 2000);
      }
    } catch (error) {
      setPhase("error");
      const msg = error instanceof Error ? error.message : "Upload failed";
      setErrorMessage(msg);
      toast.error(msg);
    }
  };

  const handleDismiss = () => {
    stopPolling();
    setOpen(false);
    resetState();
    router.refresh();
    toast.info("Processing continues in the background");
  };

  const handleRetry = () => {
    resetState();
  };

  const isProcessingActive = phase === "uploading" || phase === "processing";

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button>
          <IconUpload className="mr-2 h-4 w-4" />
          Upload File
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>
              {phase === "processing" || phase === "done"
                ? "Processing Document"
                : phase === "error"
                ? "Upload Failed"
                : "Upload File"}
            </DialogTitle>
            <DialogDescription>
              {phase === "idle" && "Select a PDF to upload to this collection."}
              {phase === "uploading" && `Uploading ${selectedFile?.name}...`}
              {phase === "processing" && (
                <>
                  <span className="font-medium">{selectedFile?.name}</span>
                  {" — you can dismiss and processing will continue in the background."}
                </>
              )}
              {phase === "done" && `${selectedFile?.name} is ready to query.`}
              {phase === "error" && errorMessage}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {phase === "idle" && (
              <div className="grid gap-2">
                <Label htmlFor="file">File</Label>
                <Input
                  id="file"
                  type="file"
                  accept=".pdf"
                  onChange={handleFileChange}
                  required
                />
                {selectedFile && (
                  <p className="text-sm text-muted-foreground">
                    {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                  </p>
                )}
              </div>
            )}

            {phase === "uploading" && (
              <div className="grid gap-2">
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>Uploading</span>
                  <span>{uploadProgress}%</span>
                </div>
                <Progress value={uploadProgress} />
              </div>
            )}

            {(phase === "processing" || phase === "done") && (
              <div className="grid gap-3">
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>{processingMessage}</span>
                  <span>{processingProgress}%</span>
                </div>
                <Progress value={processingProgress} />
                {phase === "done" && (
                  <div className="flex items-center gap-2 text-sm text-green-600">
                    <IconCheck className="h-4 w-4" />
                    Embedded and indexed — closing...
                  </div>
                )}
              </div>
            )}

            {phase === "error" && (
              <div className="flex items-center gap-2 text-sm text-destructive">
                <IconX className="h-4 w-4" />
                {errorMessage || "An unexpected error occurred."}
              </div>
            )}
          </div>

          <DialogFooter className="gap-2">
            {phase === "idle" && (
              <>
                <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={!selectedFile}>
                  Upload
                </Button>
              </>
            )}

            {phase === "uploading" && (
              <Button type="button" variant="outline" disabled>
                Uploading...
              </Button>
            )}

            {phase === "processing" && (
              <Button type="button" variant="outline" onClick={handleDismiss}>
                Dismiss
              </Button>
            )}

            {phase === "error" && (
              <>
                <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                  Close
                </Button>
                <Button type="button" onClick={handleRetry}>
                  Try Again
                </Button>
              </>
            )}
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
