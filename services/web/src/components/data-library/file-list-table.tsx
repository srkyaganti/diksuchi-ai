"use client";

import { useState } from "react";
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { FileStatusBadge } from "./file-status-badge";
import { IconDotsVertical, IconDownload, IconTrash } from "@tabler/icons-react";
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
}

export function FileListTable({ files }: FileListTableProps) {
  const router = useRouter();
  const [deletingId, setDeletingId] = useState<string | null>(null);

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
    });
  };

  if (files.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <p className="text-lg font-medium">No files yet</p>
        <p className="text-sm text-muted-foreground mt-1">
          Upload your first file to get started
        </p>
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
            <TableHead>Status</TableHead>
            <TableHead>Uploaded</TableHead>
            <TableHead className="w-[70px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {files.map((file) => (
            <TableRow key={file.id}>
              <TableCell className="font-medium">{file.name}</TableCell>
              <TableCell>{formatFileSize(file.fileSize)}</TableCell>
              <TableCell>
                <FileStatusBadge
                  status={file.status as any}
                  ragStatus={file.ragStatus as any}
                />
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
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
