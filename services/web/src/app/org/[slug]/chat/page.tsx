"use client";

import { useState, useEffect } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { useChat } from "@ai-sdk/react";
import {
  DefaultChatTransport,
  isTextUIPart,
  isReasoningUIPart,
  isFileUIPart,
  isToolOrDynamicToolUIPart,
} from "ai";
import type { UIMessage, ToolUIPart } from "ai";
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
  MessageAttachment,
} from "@/components/ai-elements/message";
import {
  Reasoning,
  ReasoningTrigger,
  ReasoningContent,
} from "@/components/ai-elements/reasoning";
import {
  Tool,
  ToolHeader,
  ToolContent,
  ToolInput,
  ToolOutput,
} from "@/components/ai-elements/tool";
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

type SourceUrlPartExtended = Extract<
  UIMessage["parts"][number],
  { type: "source-url" }
> & {
  snippet?: string;
  relevance?: string;
};

type SourceDocumentPart = Extract<
  UIMessage["parts"][number],
  { type: "source-document" }
>;

type SourcePart = SourceUrlPartExtended | SourceDocumentPart;

interface SessionApiMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  createdAt: string;
}

export default function ChatPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const orgSlug = params.slug as string;

  const [collectionId, setCollectionId] = useState<string>("");
  const [sessionId, setSessionId] = useState<string>("");
  const [isRecording, setIsRecording] = useState(false);
  const [languageCode, setLanguageCode] = useState<string>("");
  const [allMessages, setAllMessages] = useState<UIMessage[]>([]);
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
        const formattedMessages: UIMessage[] = session.messages.map(
          (msg: SessionApiMessage) => ({
            id: msg.id,
            role: msg.role,
            parts: msg.content
              ? [{ type: "text" as const, text: msg.content }]
              : [],
          })
        );
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
  const [messages, setMessages] = useState<UIMessage[]>(allMessages);

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
  const extractTextContent = (parts: UIMessage["parts"]): string => {
    if (!parts || !Array.isArray(parts)) {
      return "";
    }

    return parts
      .filter(isTextUIPart)
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
                {/* Render sources (url + document) if present */}
                {message.role === "assistant" &&
                  message.parts &&
                  (() => {
                    const sourceParts = message.parts.filter(
                      (part): part is SourcePart =>
                        part.type === "source-url" ||
                        part.type === "source-document"
                    );
                    if (sourceParts.length === 0) return null;
                    return (
                      <Sources className="mb-2">
                        <SourcesTrigger count={sourceParts.length} />
                        {sourceParts.map((part, i) => (
                          <SourcesContent key={`${message.id}-source-${i}`}>
                            {part.type === "source-url" ? (
                              <Source
                                href={part.url}
                                title={part.title}
                                className="flex flex-col gap-1"
                              >
                                <span className="font-medium">
                                  {part.title}
                                </span>
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
                            ) : (
                              <div className="flex flex-col gap-1 rounded-md border p-2">
                                <span className="font-medium">
                                  {part.title}
                                </span>
                                {part.filename && (
                                  <span className="text-xs text-muted-foreground">
                                    {part.filename}
                                  </span>
                                )}
                              </div>
                            )}
                          </SourcesContent>
                        ))}
                      </Sources>
                    );
                  })()}

                {/* Render message content */}
                <Message from={message.role}>
                  <MessageContent>
                    {message.parts &&
                      message.parts.map((part, i) => {
                        if (isTextUIPart(part)) {
                          return (
                            <MessageResponse key={`${message.id}-text-${i}`}>
                              {part.text}
                            </MessageResponse>
                          );
                        }
                        if (isFileUIPart(part)) {
                          return (
                            <MessageAttachment
                              key={`${message.id}-file-${i}`}
                              data={part}
                            />
                          );
                        }
                        if (isReasoningUIPart(part)) {
                          return (
                            <Reasoning
                              key={`${message.id}-reasoning-${i}`}
                              isStreaming={part.state === "streaming"}
                            >
                              <ReasoningTrigger />
                              <ReasoningContent>
                                {part.text}
                              </ReasoningContent>
                            </Reasoning>
                          );
                        }
                        if (isToolOrDynamicToolUIPart(part)) {
                          const toolName =
                            part.type === "dynamic-tool"
                              ? part.toolName
                              : part.type.replace(/^tool-/, "");
                          return (
                            <Tool key={`${message.id}-tool-${i}`}>
                              <ToolHeader
                                title={toolName}
                                type={`tool-${toolName}` as ToolUIPart["type"]}
                                state={part.state}
                              />
                              <ToolContent>
                                <ToolInput input={part.input} />
                                {part.state === "output-available" && (
                                  <ToolOutput
                                    output={part.output}
                                    errorText={undefined}
                                  />
                                )}
                                {part.state === "output-error" && (
                                  <ToolOutput
                                    output={undefined}
                                    errorText={part.errorText}
                                  />
                                )}
                              </ToolContent>
                            </Tool>
                          );
                        }
                        if (part.type === "step-start") {
                          return (
                            <hr
                              key={`${message.id}-step-${i}`}
                              className="my-4 border-border"
                            />
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
