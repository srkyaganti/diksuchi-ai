"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";

interface Collection {
  id: string;
  name: string;
  description?: string;
}

interface CollectionSelectorProps {
  onSelect: (collectionId: string) => void;
  defaultValue?: string;
  orgSlug?: string; // Organization slug for context-aware links
}

export function CollectionSelector({
  onSelect,
  defaultValue,
  orgSlug,
}: CollectionSelectorProps) {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedValue, setSelectedValue] = useState<string>(defaultValue || "");

  useEffect(() => {
    const fetchCollections = async () => {
      try {
        const response = await fetch("/api/collections");
        if (!response.ok) {
          throw new Error("Failed to fetch collections");
        }
        const data = await response.json();
        setCollections(data);
        if (!defaultValue && data.length > 0) {
          const firstId = data[0].id;
          setSelectedValue(firstId);
          onSelect(firstId);
        }
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to load collections";
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    fetchCollections();
  }, []);

  // Update selected value when defaultValue changes
  useEffect(() => {
    if (defaultValue) {
      setSelectedValue(defaultValue);
    }
  }, [defaultValue]);

  const handleValueChange = (value: string) => {
    console.log("Collection selected:", value);
    setSelectedValue(value);
    onSelect(value);
  };

  if (loading) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-md">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span className="text-sm">Loading collections...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="px-3 py-2 bg-red-50 rounded-md text-sm text-red-600">
        {error}
      </div>
    );
  }

  if (collections.length === 0) {
    // Use org-specific data library if orgSlug is provided, otherwise use global
    const dataLibraryUrl = orgSlug ? `/org/${orgSlug}/data-library` : "/data-library";

    return (
      <div className="flex items-center justify-between gap-2 px-3 py-2 bg-yellow-50 rounded-md">
        <span className="text-sm text-yellow-600">No collections found. Create one to get started.</span>
        <Link href={dataLibraryUrl}>
          <Button size="sm" variant="outline" className="whitespace-nowrap">
            Go to Data Library
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <Select onValueChange={handleValueChange} value={selectedValue}>
      <SelectTrigger className="w-full">
        <SelectValue placeholder="Select a collection..." />
      </SelectTrigger>
      <SelectContent>
        {collections.map((collection) => (
          <SelectItem key={collection.id} value={collection.id}>
            {collection.name}
            {collection.description && (
              <span className="text-xs text-gray-500 ml-2">
                • {collection.description}
              </span>
            )}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
