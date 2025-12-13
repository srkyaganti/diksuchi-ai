"use client";

import { useState, useEffect } from "react";
import { ChatHistoryTable } from "@/components/org/chat-history-table";
import { toast } from "sonner";

export default function ChatHistoryPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [orgSlug, setOrgSlug] = useState("");

  const loadChatSessions = async () => {
    try {
      setLoading(true);
      const { slug } = await params;
      setOrgSlug(slug);
      
      const response = await fetch(`/api/org/${slug}/chat-sessions`);
      if (response.ok) {
        const data = await response.json();
        setSessions(data.sessions || []);
      } else {
        toast.error("Failed to load chat sessions");
      }
    } catch (error) {
      console.error("Error loading chat sessions:", error);
      toast.error("Failed to load chat sessions");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSession = async (sessionId: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/chat/sessions/${sessionId}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        toast.success("Chat session deleted successfully");
        // Reload sessions to update the table
        await loadChatSessions();
      } else {
        const error = await response.json();
        toast.error(error.error || "Failed to delete chat session");
      }
    } catch (error) {
      console.error("Error deleting chat session:", error);
      toast.error("Failed to delete chat session");
    } finally {
      setLoading(false);
    }
  };

  // Load sessions on component mount
  useEffect(() => {
    loadChatSessions();
  }, []);

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:gap-6 md:p-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Chat History</h1>
        <p className="text-muted-foreground">
          View and manage your chat sessions
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
            <p className="text-sm text-gray-600">Loading chat sessions...</p>
          </div>
        </div>
      ) : (
        <ChatHistoryTable
          sessions={sessions}
          currentUserId={sessions[0]?.userId || ""}
          orgSlug={orgSlug}
          onDeleteSession={handleDeleteSession}
        />
      )}
    </div>
  );
}