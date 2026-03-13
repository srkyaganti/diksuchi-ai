"use client";

import { useState, useEffect, useCallback } from "react";
import {
  IconFolder,
  IconFolderOpen,
  IconFile,
  IconChevronRight,
  IconChevronDown,
  IconLoader2,
} from "@tabler/icons-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface Collection {
  id: string;
  name: string;
  description?: string;
  _count?: { files: number };
}

interface FileItem {
  id: string;
  filename: string;
  mimeType?: string;
  status?: string;
}

interface CollectionFilesPanelProps {
  orgSlug: string;
  selectedCollectionId: string;
  onSelectCollection: (collectionId: string) => void;
}

export const CollectionFilesPanel = ({
  orgSlug,
  selectedCollectionId,
  onSelectCollection,
}: CollectionFilesPanelProps) => {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [filesMap, setFilesMap] = useState<Record<string, FileItem[]>>({});
  const [loadingFiles, setLoadingFiles] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCollections = async () => {
      try {
        const response = await fetch("/api/collections");
        if (!response.ok) throw new Error("Failed to fetch collections");
        const data = await response.json();
        setCollections(data);

        if (!selectedCollectionId && data.length > 0) {
          onSelectCollection(data[0].id);
          setExpandedIds(new Set([data[0].id]));
          fetchFiles(data[0].id);
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load collections"
        );
      } finally {
        setLoading(false);
      }
    };

    fetchCollections();
  }, []);

  const fetchFiles = useCallback(
    async (collectionId: string) => {
      if (filesMap[collectionId] || loadingFiles.has(collectionId)) return;

      setLoadingFiles((prev) => new Set(prev).add(collectionId));
      try {
        const response = await fetch(
          `/api/collections/${collectionId}/files`
        );
        if (!response.ok) throw new Error("Failed to fetch files");
        const data = await response.json();
        setFilesMap((prev) => ({ ...prev, [collectionId]: data }));
      } catch {
        setFilesMap((prev) => ({ ...prev, [collectionId]: [] }));
      } finally {
        setLoadingFiles((prev) => {
          const next = new Set(prev);
          next.delete(collectionId);
          return next;
        });
      }
    },
    [filesMap, loadingFiles]
  );

  const handleToggleExpand = (collectionId: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(collectionId)) {
        next.delete(collectionId);
      } else {
        next.add(collectionId);
        fetchFiles(collectionId);
      }
      return next;
    });
  };

  const handleSelectCollection = (collectionId: string) => {
    onSelectCollection(collectionId);
    if (!expandedIds.has(collectionId)) {
      handleToggleExpand(collectionId);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32">
        <IconLoader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-sm text-destructive">{error}</div>
    );
  }

  if (collections.length === 0) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        No collections found. Create one in the Data Library.
      </div>
    );
  }

  return (
    <ScrollArea className="h-full">
      <div className="p-2">
        <h3 className="px-2 mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Collections
        </h3>
        <div className="space-y-0.5">
          {collections.map((collection) => {
            const isExpanded = expandedIds.has(collection.id);
            const isSelected = selectedCollectionId === collection.id;
            const files = filesMap[collection.id];
            const isLoadingFiles = loadingFiles.has(collection.id);
            const fileCount =
              collection._count?.files ?? files?.length ?? 0;

            return (
              <div key={collection.id}>
                <button
                  className={cn(
                    "flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors hover:bg-accent",
                    isSelected && "bg-accent font-medium"
                  )}
                  onClick={() => handleSelectCollection(collection.id)}
                  aria-label={`Select collection ${collection.name}`}
                  tabIndex={0}
                >
                  <button
                    className="shrink-0 p-0.5 rounded hover:bg-accent-foreground/10"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleToggleExpand(collection.id);
                    }}
                    aria-label={
                      isExpanded ? "Collapse collection" : "Expand collection"
                    }
                    tabIndex={0}
                  >
                    {isExpanded ? (
                      <IconChevronDown className="h-3.5 w-3.5" />
                    ) : (
                      <IconChevronRight className="h-3.5 w-3.5" />
                    )}
                  </button>
                  {isExpanded ? (
                    <IconFolderOpen className="h-4 w-4 shrink-0 text-blue-500" />
                  ) : (
                    <IconFolder className="h-4 w-4 shrink-0 text-muted-foreground" />
                  )}
                  <span className="truncate flex-1 text-left">
                    {collection.name}
                  </span>
                  <Badge
                    variant="secondary"
                    className="ml-auto text-[10px] px-1.5 py-0"
                  >
                    {fileCount}
                  </Badge>
                </button>

                {isExpanded && (
                  <div className="ml-6 mt-0.5 space-y-0.5 border-l pl-2">
                    {isLoadingFiles ? (
                      <div className="flex items-center gap-2 px-2 py-1 text-xs text-muted-foreground">
                        <IconLoader2 className="h-3 w-3 animate-spin" />
                        Loading files...
                      </div>
                    ) : files && files.length > 0 ? (
                      files.map((file) => (
                        <div
                          key={file.id}
                          className="flex items-center gap-2 rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-accent/50 transition-colors"
                        >
                          <IconFile className="h-3.5 w-3.5 shrink-0" />
                          <span className="truncate">{file.filename}</span>
                        </div>
                      ))
                    ) : (
                      <div className="px-2 py-1 text-xs text-muted-foreground">
                        No files in this collection
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </ScrollArea>
  );
};
