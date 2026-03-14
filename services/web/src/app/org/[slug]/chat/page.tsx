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
import { CollectionFilesPanel } from "@/components/chat/collection-files-panel";
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

export default function ChatPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const orgSlug = params.slug as string;

  const [collectionId, setCollectionId] = useState<string>("");
  const [collectionFileCount, setCollectionFileCount] = useState<number>(0);
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
        const formattedMessages: UIMessage[] = session.messages.map(
          (msg: { id: string; role: string; content: string; parts: any }) => ({
            id: msg.id,
            role: msg.role,
            parts: msg.parts || [{ type: "text" as const, text: msg.content }],
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

  const { sendMessage, status, regenerate, messages: chatMessages } = useChat({
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

  // Merge chatMessages from useChat with existing messages
  useEffect(() => {
    if (chatMessages.length > 0) {
      setMessages((prev) => {
        const existingIds = new Set(prev.map((m) => m.id));
        const newMsgs = chatMessages.filter((m) => !existingIds.has(m.id));
        if (newMsgs.length > 0) {
          return [...prev, ...newMsgs];
        }
        return prev;
      });
    }
  }, [chatMessages]);

  // Update allMessages when new messages are added
  useEffect(() => {
    if (messages.length > allMessages.length) {
      setAllMessages(messages);
    }
  }, [messages, allMessages.length]);

  const handleCollectionSelect = (newCollectionId: string) => {
    setCollectionId(newCollectionId);
    setSessionId("");
    setAllMessages([]);
    setMessages([]);
  };

  const handleFileCountChange = (id: string, count: number) => {
    setCollectionFileCount(count);
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
    <div className="flex h-full">
      {/* Left Panel: Collections & Files */}
      <div className="w-72 shrink-0 border-r bg-background">
        <CollectionFilesPanel
          orgSlug={orgSlug}
          selectedCollectionId={collectionId}
          onSelectCollection={handleCollectionSelect}
          onFileCountChange={handleFileCountChange}
        />
      </div>

      {/* Right Panel: Chat */}
      <div className="flex flex-1 flex-col min-w-0">
        {/* Chat Area */}
        <Conversation className="flex-1">
          <ConversationContent>
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                  <p className="text-sm text-muted-foreground">Loading chat history...</p>
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
                    : "Select a collection from the left panel to begin chatting"
                }
              />
            ) : (
              messages.map((message) => (
                <div key={message.id}>
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
        <div className="border-t p-4">
          {collectionId && collectionFileCount === 0 && (
            <div className="mb-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-800">
              This collection has no files. Upload files to the collection to start chatting.
            </div>
          )}

          {!collectionId && (
            <div className="mb-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-800">
              Select a collection from the left panel to start chatting
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
                disabled={!collectionId || collectionFileCount === 0 || status === "streaming"}
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
    </div>
  );
}
