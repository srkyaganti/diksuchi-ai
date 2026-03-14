"use client";

import dynamic from "next/dynamic";

const FileUploadDialog = dynamic(
  () =>
    import("@/components/data-library/file-upload-dialog").then(
      (mod) => mod.FileUploadDialog
    ),
  { ssr: false }
);

interface FileUploadDialogWrapperProps {
  collectionId: string;
}

export function FileUploadDialogWrapper({
  collectionId,
}: FileUploadDialogWrapperProps) {
  return <FileUploadDialog collectionId={collectionId} />;
}
