"use client";

import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { IconFolder, IconDotsVertical, IconTrash } from "@tabler/icons-react";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { useState } from "react";

interface Collection {
  id: string;
  name: string;
  description: string | null;
  createdAt: string;
  _count: {
    files: number;
  };
}

interface CollectionCardProps {
  collection: Collection;
  orgSlug?: string;
}

export function CollectionCard({ collection, orgSlug }: CollectionCardProps) {
  const router = useRouter();
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (!confirm(`Are you sure you want to delete "${collection.name}"?`)) {
      return;
    }

    setIsDeleting(true);

    try {
      const response = await fetch(`/api/collections/${collection.id}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Failed to delete collection");
      }

      toast.success("Collection deleted successfully");
      router.refresh();
    } catch (error) {
      console.error("Error deleting collection:", error);
      toast.error("Failed to delete collection");
    } finally {
      setIsDeleting(false);
    }
  };

  const href = orgSlug
    ? `/org/${orgSlug}/data-library/${collection.id}`
    : `/data-library/${collection.id}`;

  return (
    <Link href={href}>
      <Card className="hover:bg-accent/50 transition-colors cursor-pointer">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-primary/10 p-2">
                <IconFolder className="h-6 w-6 text-primary" />
              </div>
              <div>
                <CardTitle className="text-lg">{collection.name}</CardTitle>
                <CardDescription className="text-sm mt-1">
                  {collection._count.files} {collection._count.files === 1 ? "file" : "files"}
                </CardDescription>
              </div>
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                  <IconDotsVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  onClick={handleDelete}
                  disabled={isDeleting}
                  className="text-destructive"
                >
                  <IconTrash className="mr-2 h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardHeader>
        {collection.description && (
          <CardContent>
            <p className="text-sm text-muted-foreground line-clamp-2">
              {collection.description}
            </p>
          </CardContent>
        )}
      </Card>
    </Link>
  );
}
