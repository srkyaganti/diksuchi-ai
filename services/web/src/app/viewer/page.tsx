"use client";

import { useSearchParams } from "next/navigation";
import { useMemo, Suspense } from "react";

function PDFViewerContent() {
  const searchParams = useSearchParams();

  const fileId = searchParams.get("fileId");
  const page = searchParams.get("page") || "1";
  const fileName = searchParams.get("name") || "Document";

  const pdfUrl = useMemo(() => {
    if (!fileId) return "";
    return `/api/files/${fileId}/view#page=${page}`;
  }, [fileId, page]);

  if (!fileId) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <p className="text-lg font-medium text-muted-foreground">
            No file specified
          </p>
          <p className="text-sm text-muted-foreground mt-1">
            Please provide a fileId query parameter.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header bar */}
      <div className="flex items-center justify-between border-b px-4 py-2 bg-background shrink-0">
        <div className="flex items-center gap-3">
          <h1 className="text-sm font-medium truncate max-w-md">
            {fileName}
          </h1>
          {page && page !== "1" && (
            <span className="text-xs bg-secondary text-secondary-foreground px-2 py-0.5 rounded">
              Page {page}
            </span>
          )}
        </div>
        <button
          onClick={() => window.close()}
          className="text-xs text-muted-foreground hover:text-foreground transition-colors px-2 py-1 rounded hover:bg-accent"
        >
          Close
        </button>
      </div>

      {/* PDF embed */}
      <div className="flex-1 overflow-hidden">
        <embed
          src={pdfUrl}
          type="application/pdf"
          width="100%"
          height="100%"
          className="border-0"
        />
      </div>
    </div>
  );
}

export default function ViewerPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">Loading viewer...</p>
          </div>
        </div>
      }
    >
      <PDFViewerContent />
    </Suspense>
  );
}
