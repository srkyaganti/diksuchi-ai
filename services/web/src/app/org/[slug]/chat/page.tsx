"use client";

import { useState, useEffect } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
  ConversationEmptyState,
} from "@/components/ai-elements/conversation";
import {
  Message,
  MessageContent,
  MessageResponse,
  MessageActions,
  MessageAction,
} from "@/components/ai-elements/message";
import {
  PromptInput,
  PromptInputBody,
  PromptInputTextarea,
  PromptInputFooter,
  PromptInputTools,
  PromptInputSubmit,
  PromptInputHeader,
  PromptInputAttachments,
  PromptInputAttachment,
  PromptInputActionMenu,
  PromptInputActionMenuTrigger,
  PromptInputActionMenuContent,
  PromptInputActionAddAttachments,
  type PromptInputMessage,
} from "@/components/ai-elements/prompt-input";
import {
  Sources,
  SourcesTrigger,
  SourcesContent,
  Source,
} from "@/components/ai-elements/sources";
import { CollectionSelector } from "@/components/chat/collection-selector";
import { VoiceInput } from "@/components/chat/voice-input";
import { VoiceOutput } from "@/components/chat/voice-output";
import { toast } from "sonner";
import { CopyIcon, RefreshCcwIcon } from "lucide-react";

export default function ChatPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const orgSlug = params.slug as string;

  const [collectionId, setCollectionId] = useState<string>("");
  const [sessionId, setSessionId] = useState<string>("");
  const [isRecording, setIsRecording] = useState(false);
  const [languageCode, setLanguageCode] = useState<string>("");
  const [allMessages, setAllMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Extract sessionId from URL search parameters
  useEffect(() => {
    const urlSessionId = searchParams.get("sessionId");
    if (urlSessionId) {
      setSessionId(urlSessionId);
      loadExistingMessages(urlSessionId);
    } else {
      setLoading(false);
    }
  }, [searchParams]);

  const loadExistingMessages = async (sessionToLoad: string) => {
    try {
      const response = await fetch(`/api/chat/sessions/${sessionToLoad}`);
      if (response.ok) {
        const session = await response.json();
        // Convert messages to the format expected by useChat
        const formattedMessages = session.messages.map((msg: any) => ({
          id: msg.id,
          role: msg.role,
          parts: msg.content ? [{ type: "text", text: msg.content }] : [],
          createdAt: msg.createdAt,
        }));
        setAllMessages(formattedMessages);
      }
    } catch (error) {
      console.error("Error loading existing messages:", error);
    } finally {
      setLoading(false);
    }
  };

  const { sendMessage, status, regenerate } = useChat({
    transport: new DefaultChatTransport({
      api: "/api/chat",
    }),
    onError: (error) => {
      console.error("Chat error:", error);
      toast.error("Failed to send message: " + error.message);
    },
  });

  // Combine existing messages with new messages from useChat
  const [messages, setMessages] = useState<any[]>(allMessages);

  // Update messages when allMessages change (from existing chat load)
  useEffect(() => {
    setMessages(allMessages);
  }, [allMessages]);

  // Update allMessages when new messages are added by useChat
  useEffect(() => {
    if (messages.length > allMessages.length) {
      setAllMessages(messages);
    }
  }, [messages, allMessages.length]);

  const handleCollectionSelect = (newCollectionId: string) => {
    setCollectionId(newCollectionId);
    // Reset chat when switching collections
    setSessionId("");
    setAllMessages([]);
    setMessages([]);
  };

  const handleVoiceTranscribed = ({
    text,
    languageCode,
  }: {
    text: string;
    languageCode: string;
  }) => {
    // Submit voice input as a message
    if (!collectionId) {
      toast.error("Please select a collection first");
      return;
    }

    setLanguageCode(languageCode);

    sendMessage(
      { text },
      {
        body: { collectionId, sessionId: sessionId || undefined },
      }
    );
  };

  const handleSubmit = (message: PromptInputMessage) => {
    if (!collectionId) {
      toast.error("Please select a collection first");
      return;
    }

    const hasText = Boolean(message.text);
    const hasAttachments = Boolean(message.files?.length);

    if (!(hasText || hasAttachments)) {
      return;
    }

    sendMessage(
      {
        text: message.text || "Sent with attachments",
        files: message.files,
      },
      {
        body: {
          collectionId,
          sessionId: sessionId || undefined,
        },
      }
    );
  };

  // Extract text from message parts for voice output
  const extractTextContent = (parts: any[]): string => {
    if (!parts || !Array.isArray(parts)) {
      return "";
    }

    return parts
      .filter((part) => part.type === "text")
      .map((part) => part.text)
      .join("\n");
  };

  // Get last assistant message for voice output
  const lastAssistantMessage = messages
    .slice()
    .reverse()
    .find((msg) => msg.role === "assistant");

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-semibold">Chat with Your Documents</h1>
          <div className="w-20" /> {/* Spacer */}
        </div>

        {/* Collection Selector */}
        <div className="max-w-md">
          <label className="block text-sm font-medium mb-2">
            Select Collection
          </label>
          <CollectionSelector
            onSelect={handleCollectionSelect}
            defaultValue={collectionId}
            orgSlug={orgSlug}
          />
        </div>
      </div>
        {/* Main Chat Area */}
      <Conversation className="flex-1">
        <ConversationContent>
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                <p className="text-sm text-gray-600">Loading chat history...</p>
              </div>
            </div>
          ) : messages.length === 0 ? (
            <ConversationEmptyState
              title="Welcome to RAG Chat"
              description={
                collectionId
                  ? sessionId
                    ? "Your previous conversation will appear here. Start asking new questions!"
                    : "Start asking questions about your documents or upload files to analyze"
                  : "Please select a collection above to begin chatting"
              }
            />
          ) : (
            messages.map((message) => (
              <div key={message.id}>
                {/* Render sources first if present */}
                {message.role === "assistant" &&
                  message.parts &&
                  message.parts.filter((part) => part.type === "source-url")
                    .length > 0 && (
                    <Sources className="mb-2">
                      <SourcesTrigger
                        count={
                          message.parts.filter((part) => part.type === "source-url")
                            .length
                        }
                      />
                      {message.parts
                        .filter((part) => part.type === "source-url")
                        .map((part: any, i) => (
                          <SourcesContent key={`${message.id}-source-${i}`}>
                            <Source
                              href={part.url}
                              title={part.title}
                              className="flex flex-col gap-1"
                            >
                              <span className="font-medium">{part.title}</span>
                              {part.snippet && (
                                <span className="text-xs text-muted-foreground line-clamp-2">
                                  {part.snippet}
                                </span>
                              )}
                              {part.relevance && (
                                <span className="text-xs text-blue-600">
                                  Relevance: {part.relevance}
                                </span>
                              )}
                            </Source>
                          </SourcesContent>
                        ))}
                    </Sources>
                  )}

                {/* Render message content */}
                <Message from={message.role}>
                  <MessageContent>
                    {message.parts &&
                      message.parts.map((part, i) => {
                        if (part.type === "text") {
                          return (
                            <MessageResponse key={`${message.id}-text-${i}`}>
                              {part.text}
                            </MessageResponse>
                          );
                        }
                        if (part.type === "file") {
                          return (
                            <div
                              key={`${message.id}-file-${i}`}
                              className="mb-2"
                            >
                              {part.mediaType?.startsWith("image/") ? (
                                <img
                                  src={part.url}
                                  alt={part.filename || "Uploaded image"}
                                  className="max-w-sm rounded-lg"
                                />
                              ) : (
                                <div className="p-3 bg-gray-100 rounded border">
                                  <span className="text-sm">
                                    📎 {part.filename || "File"}
                                  </span>
                                </div>
                              )}
                            </div>
                          );
                        }
                        return null;
                      })}
                  </MessageContent>

                  {/* Message actions for assistant messages */}
                  {message.role === "assistant" &&
                    message.id === messages[messages.length - 1]?.id && (
                      <MessageActions>
                        <MessageAction
                          onClick={() => regenerate()}
                          label="Retry"
                        >
                          <RefreshCcwIcon className="size-3" />
                        </MessageAction>
                        <MessageAction
                          onClick={() =>
                            navigator.clipboard.writeText(
                              extractTextContent(message.parts)
                            )
                          }
                          label="Copy"
                        >
                          <CopyIcon className="size-3" />
                        </MessageAction>
                      </MessageActions>
                    )}
                </Message>
              </div>
            ))
          )}
        </ConversationContent>

        <ConversationScrollButton />
      </Conversation>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 p-4">
        {!collectionId && (
          <div className="mb-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-800">
            ⚠️ Please select a collection above to start chatting
          </div>
        )}

        <PromptInput
          onSubmit={handleSubmit}
          className="mb-3"
          globalDrop
          multiple
        >
          <PromptInputHeader>
            <PromptInputAttachments>
              {(attachment) => <PromptInputAttachment data={attachment} />}
            </PromptInputAttachments>
          </PromptInputHeader>

          <PromptInputBody>
            <PromptInputTextarea
              placeholder="Ask a question about your documents or upload files..."
              disabled={!collectionId || status === "streaming"}
            />
          </PromptInputBody>

          <PromptInputFooter>
            <PromptInputTools>
              <PromptInputActionMenu>
                <PromptInputActionMenuTrigger />
                <PromptInputActionMenuContent>
                  <PromptInputActionAddAttachments />
                </PromptInputActionMenuContent>
              </PromptInputActionMenu>

              {/* Voice Input Button */}
              <VoiceInput
                onTranscribed={handleVoiceTranscribed}
                isDisabled={!collectionId || status === "streaming"}
              />
            </PromptInputTools>

            <PromptInputSubmit
              status={status}
              disabled={!collectionId || status === "streaming"}
            />
          </PromptInputFooter>
        </PromptInput>

        {/* Auto-play voice output for last assistant message */}
        {lastAssistantMessage && lastAssistantMessage.parts && (
          <VoiceOutput
            text={extractTextContent(lastAssistantMessage.parts)}
            languageCode={languageCode}
            isDisabled={status === "streaming"}
            autoPlay={true}
          />
        )}
      </div>
    </div>
  );
}
