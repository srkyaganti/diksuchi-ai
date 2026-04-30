"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { FileStatusBadge } from "./file-status-badge";
import { IconDotsVertical, IconDownload, IconTrash, IconUpload } from "@tabler/icons-react";
import { toast } from "sonner";

interface File {
  id: string;
  name: string;
  fileSize: bigint;
  mimeType: string;
  status: string;
  ragStatus: string | null;
  uploadedAt: string;
}

interface FileListTableProps {
  files: File[];
  collectionId: string;
}

interface JobProgress {
  progress: number;
  message: string;
}

const STEP_LABELS: Record<string, string> = {
  "Starting document processing": "Starting...",
  "Running Docling PDF conversion": "Converting PDF...",
  "Docling conversion complete": "PDF converted",
  "Building section map": "Mapping structure",
  "Mapping images to sections": "Locating images",
  "Image metadata built": "Images mapped",
  "Saving document to storage": "Saving...",
  "Chunking document by sections": "Splitting into chunks",
  "Building BM25 keyword index": "Building keyword index",
  "Document processing completed": "Done!",
};

function friendlyMessage(raw: string | undefined): string {
  if (!raw) return "Processing...";
  if (raw.startsWith("Captioning image") || raw.startsWith("Embedding chunks")) return raw;
  return STEP_LABELS[raw] ?? raw;
}

export function FileListTable({ files, collectionId }: FileListTableProps) {
  const router = useRouter();
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [jobProgress, setJobProgress] = useState<Record<string, JobProgress>>({});
  const pollingRefs = useRef<Record<string, ReturnType<typeof setInterval>>>({});

  const stopPollingFile = (fileId: string) => {
    if (pollingRefs.current[fileId]) {
      clearInterval(pollingRefs.current[fileId]);
      delete pollingRefs.current[fileId];
    }
  };

  const startPollingFile = (fileId: string) => {
    if (pollingRefs.current[fileId]) return;
    const jobId = `${collectionId}-${fileId}`;
    pollingRefs.current[fileId] = setInterval(async () => {
      try {
        const res = await fetch(`/api/jobs/${jobId}`);
        if (!res.ok) return;
        const data = await res.json();

        setJobProgress((prev) => ({
          ...prev,
          [fileId]: {
            progress: data.progress ?? 0,
            message: friendlyMessage(data.message),
          },
        }));

        if (data.status === "completed" || data.status === "failed") {
          stopPollingFile(fileId);
          router.refresh();
        }
      } catch {
        // Ignore transient polling errors
      }
    }, 2000);
  };

  useEffect(() => {
    // Poll any file that is not in a terminal state. ragStatus starts at
    // "none" right after upload (job is queued in RQ but the worker hasn't
    // flipped it to "processing" yet); without this, the bar wouldn't appear
    // until a manual refresh.
    const isTerminal = (s: string | null) => s === "completed" || s === "failed";
    files
      .filter((f) => !isTerminal(f.ragStatus))
      .forEach((f) => startPollingFile(f.id));

    return () => {
      Object.keys(pollingRefs.current).forEach(stopPollingFile);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [files, collectionId]);

  const handleDownload = async (fileId: string, fileName: string) => {
    try {
      const response = await fetch(`/api/files/${fileId}/download`);

      if (!response.ok) {
        throw new Error("Failed to download file");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success("File downloaded successfully");
    } catch (error) {
      console.error("Error downloading file:", error);
      toast.error("Failed to download file");
    }
  };

  const handleDelete = async (fileId: string, fileName: string) => {
    if (!confirm(`Are you sure you want to delete "${fileName}"?`)) {
      return;
    }

    setDeletingId(fileId);

    try {
      const response = await fetch(`/api/files/${fileId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Failed to delete file");
      }

      toast.success("File deleted successfully");
      router.refresh();
    } catch (error) {
      console.error("Error deleting file:", error);
      toast.error("Failed to delete file");
    } finally {
      setDeletingId(null);
    }
  };

  const formatFileSize = (bytes: bigint) => {
    const mb = Number(bytes) / (1024 * 1024);
    if (mb < 1) {
      return `${(Number(bytes) / 1024).toFixed(2)} KB`;
    }
    return `${mb.toFixed(2)} MB`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "UTC",
    });
  };

  if (files.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-muted-foreground/25 p-12 flex flex-col items-center justify-center min-h-[500px]">
        <div className="flex flex-col items-center justify-center text-center">
          <div className="flex justify-center mb-4">
            <div className="rounded-full bg-muted p-4">
              <IconUpload className="h-6 w-6 text-muted-foreground" />
            </div>
          </div>
          <h3 className="text-lg font-semibold">No files yet</h3>
          <p className="text-sm text-muted-foreground mt-2">
            Upload documents to start analyzing with AI-powered retrieval
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Size</TableHead>
            <TableHead className="min-w-[200px]">Status</TableHead>
            <TableHead>Uploaded</TableHead>
            <TableHead className="w-[70px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {files.map((file) => {
            const progress = jobProgress[file.id];

            return (
              <TableRow key={file.id}>
                <TableCell className="font-medium">{file.name}</TableCell>
                <TableCell>{formatFileSize(file.fileSize)}</TableCell>
                <TableCell>
                  {progress ? (
                    <div className="grid gap-1 w-full max-w-[220px]">
                      <div className="flex items-center justify-between gap-2 text-xs text-muted-foreground">
                        <span className="truncate">{progress.message}</span>
                        <span className="shrink-0 tabular-nums">{progress.progress}%</span>
                      </div>
                      <Progress value={progress.progress} className="h-1.5" />
                    </div>
                  ) : (
                    <FileStatusBadge
                      status={file.status as any}
                      ragStatus={file.ragStatus as any}
                    />
                  )}
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {formatDate(file.uploadedAt)}
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0"
                        disabled={deletingId === file.id}
                      >
                        <IconDotsVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        onClick={() => handleDownload(file.id, file.name)}
                      >
                        <IconDownload className="mr-2 h-4 w-4" />
                        Download
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => handleDelete(file.id, file.name)}
                        className="text-destructive"
                      >
                        <IconTrash className="mr-2 h-4 w-4" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
