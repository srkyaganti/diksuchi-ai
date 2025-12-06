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
}

export function ChatHistoryTable({
  sessions,
  currentUserId,
  orgSlug,
}: ChatHistoryTableProps) {
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
                  {session.title || "Untitled Chat"}
                </TableCell>
                <TableCell>{session.collection.name}</TableCell>
                <TableCell>
                  {session.userId === currentUserId ? "You" : session.user.name}
                </TableCell>
                <TableCell>
                  {formatDistanceToNow(new Date(session.updatedAt), {
                    addSuffix: true,
                  })}
                </TableCell>
                <TableCell className="text-right">
                  <Button variant="ghost" size="sm" asChild>
                    <Link
                      href={`/org/${orgSlug}/chat?sessionId=${session.id}`}
                    >
                      View
                    </Link>
                  </Button>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}
