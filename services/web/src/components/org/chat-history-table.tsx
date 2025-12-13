"use client";

import Link from "next/link";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Trash2Icon } from "lucide-react";
import { toast } from "sonner";
import { formatDistanceToNow } from "date-fns";

interface ChatHistoryTableProps {
  sessions: Array<{
    id: string;
    title: string | null;
    userId: string;
    updatedAt: Date;
    user: {
      id: string;
      name: string;
      email: string;
    };
    collection: {
      id: string;
      name: string;
    };
  }>;
  currentUserId: string;
  orgSlug: string;
  onDeleteSession?: (sessionId: string) => void;
}

export function ChatHistoryTable({
  sessions,
  currentUserId,
  orgSlug,
  onDeleteSession,
}: ChatHistoryTableProps) {
  // Ensure we have valid data
  const validSessions = sessions || [];
  const validCurrentUserId = currentUserId || "";
  const validOrgSlug = orgSlug || "";
  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Title</TableHead>
            <TableHead>Collection</TableHead>
            <TableHead>Created By</TableHead>
            <TableHead>Last Updated</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sessions.length === 0 ? (
            <TableRow>
              <TableCell
                colSpan={5}
                className="text-center text-muted-foreground"
              >
                No chat sessions found
              </TableCell>
            </TableRow>
          ) : (
            sessions.map((session) => (
              <TableRow key={session.id}>
                <TableCell className="font-medium">
                  {session?.title || "Untitled Chat"}
                </TableCell>
                <TableCell>{session?.collection?.name || "Unknown Collection"}</TableCell>
                <TableCell>
                  {session?.userId === validCurrentUserId ? "You" : session?.user?.name || "Unknown User"}
                </TableCell>
                <TableCell>
                  {session?.updatedAt ? formatDistanceToNow(new Date(session.updatedAt), {
                    addSuffix: true,
                  }) : "Unknown time"}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-2">
                    <Button variant="ghost" size="sm" asChild>
                      <Link
                        href={`/org/${validOrgSlug}/chat?sessionId=${session.id}`}
                      >
                        Open
                      </Link>
                    </Button>
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button variant="ghost" size="sm" className="text-destructive hover:text-destructive">
                          <Trash2Icon className="h-4 w-4" />
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Delete Chat Session</DialogTitle>
                          <DialogDescription>
                            Are you sure you want to delete the chat session "{session?.title || 'Untitled Chat'}"? 
                            This action cannot be undone and will permanently delete all associated messages.
                          </DialogDescription>
                        </DialogHeader>
                        <DialogFooter>
                          <DialogClose asChild>
                            <Button variant="outline">Cancel</Button>
                          </DialogClose>
                          <Button 
                            variant="destructive" 
                            onClick={() => {
                              if (onDeleteSession) {
                                onDeleteSession(session.id);
                              }
                            }}
                          >
                            Delete
                          </Button>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                  </div>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}
