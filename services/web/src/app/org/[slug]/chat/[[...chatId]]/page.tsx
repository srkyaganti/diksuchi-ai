"use client";

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import { useChat } from "@ai-sdk/react";
import {
  DefaultChatTransport,
  isTextUIPart,
  isReasoningUIPart,
  isFileUIPart,
  isToolOrDynamicToolUIPart,
} from "ai";
import type { UIMessage, ToolUIPart, ChatStatus } from "ai";
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
  PromptInputProvider,
  usePromptInputController,
  type PromptInputMessage,
} from "@/components/ai-elements/prompt-input";
import {
  Sources,
  SourcesTrigger,
  SourcesContent,
} from "@/components/ai-elements/sources";
import { CollectionFilesPanel } from "@/components/chat/collection-files-panel";
import { VoiceInput } from "@/components/chat/voice-input";
import { VoiceOutput } from "@/components/chat/voice-output";
import { toast } from "sonner";
import { CopyIcon, ZoomInIcon, ZoomOutIcon, FileTextIcon, ExternalLinkIcon } from "lucide-react";

interface SourceRef {
  fileId: string | null;
  fileName: string;
  sectionPath: string;
  pageNo: number | null;
  documentUuid: string;
}

function DocumentImage({ src, alt }: { src: string; alt: string }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="my-2">
      <div className="relative inline-block">
        <img
          src={src}
          alt={alt}
          className="max-w-full rounded-lg border cursor-pointer hover:opacity-90 transition"
          style={{
            maxHeight: expanded ? "none" : "400px",
            objectFit: "contain",
          }}
          onClick={() => setExpanded(!expanded)}
        />
        <button
          onClick={() => setExpanded(!expanded)}
          className="absolute top-2 right-2 rounded-full bg-background/80 p-1 backdrop-blur-sm hover:bg-background transition-opacity opacity-0 group-hover:opacity-100"
          style={{ opacity: 0.7 }}
          type="button"
        >
          {expanded ? (
            <ZoomOutIcon className="size-4" />
          ) : (
            <ZoomInIcon className="size-4" />
          )}
        </button>
      </div>
      {alt && alt !== "Document image" && (
        <p className="text-xs text-muted-foreground mt-1">{alt}</p>
      )}
    </div>
  );
}

function ChatInput({
  collectionId,
  collectionFileCount,
  status,
  languageCode,
  lastAssistantText,
  onSubmit,
  onVoiceTranscribed,
}: {
  collectionId: string;
  collectionFileCount: number;
  status: ChatStatus;
  languageCode: string;
  lastAssistantText: string;
  onSubmit: (message: PromptInputMessage) => void;
  onVoiceTranscribed: (input: { text: string; languageCode: string; setInput: (value: string) => void }) => void;
}) {
  const { textInput } = usePromptInputController();

  const handleVoiceTranscribed = (input: { text: string; languageCode: string }) => {
    onVoiceTranscribed({ ...input, setInput: textInput.setInput });
  };

  return (
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
        onSubmit={onSubmit}
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
            <VoiceInput
              onTranscribed={handleVoiceTranscribed}
              isDisabled={!collectionId || status === "streaming"}
            />
            <VoiceOutput
              text={lastAssistantText}
              languageCode={languageCode}
              isDisabled={status !== "ready"}
              autoPlay={true}
            />
          </PromptInputTools>

          <PromptInputSubmit
            status={status}
            disabled={!collectionId || status === "streaming"}
          />
        </PromptInputFooter>
      </PromptInput>
    </div>
  );
}

export default function ChatPage() {
  const params = useParams();
  const router = useRouter();
  const orgSlug = params.slug as string;
  const chatIdFromUrl = (params.chatId as string[] | undefined)?.[0];

  const [collectionId, setCollectionId] = useState<string>("");
  const [collectionName, setCollectionName] = useState<string>("");
  const [collectionFileCount, setCollectionFileCount] = useState<number>(0);
  const [sessionId, setSessionId] = useState<string>("");
  const [languageCode, setLanguageCode] = useState<string>("en");
  const [loading, setLoading] = useState(true);
  const [messageSources, setMessageSources] = useState<Record<string, SourceRef[]>>({});
  const justCreatedSessionRef = useRef(false);
  const sessionIdRef = useRef<string>(sessionId);
  sessionIdRef.current = sessionId;

  // Backward-compat redirect for old ?sessionId= URLs
  useEffect(() => {
    const legacySessionId = new URLSearchParams(window.location.search).get("sessionId");
    if (legacySessionId && !chatIdFromUrl) {
      router.replace(`/org/${orgSlug}/chat/${legacySessionId}`);
    }
  }, [chatIdFromUrl, orgSlug, router]);

  // Load session from path-based chatId
  useEffect(() => {
    if (chatIdFromUrl) {
      if (justCreatedSessionRef.current) {
        justCreatedSessionRef.current = false;
        return;
      }
      setSessionId(chatIdFromUrl);
      loadExistingMessages(chatIdFromUrl);
    } else {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chatIdFromUrl]);

  const loadExistingMessages = async (sessionToLoad: string) => {
    try {
      const response = await fetch(`/api/chat/sessions/${sessionToLoad}`);
      if (!response.ok) {
        toast.error("Chat session not found");
        router.replace(`/org/${orgSlug}/chat`);
        return;
      }
      const session = await response.json();
      const formattedMessages: UIMessage[] = session.messages.map(
        (msg: { id: string; role: string; content: string; parts: unknown; sources?: unknown }) => ({
          id: msg.id,
          role: msg.role,
          parts: msg.parts || [{ type: "text" as const, text: msg.content }],
        })
      );
      setMessages(formattedMessages);

      // Extract structured sources from assistant messages
      const sourcesMap: Record<string, SourceRef[]> = {};
      for (const msg of session.messages) {
        if (msg.role === "assistant" && msg.sources) {
          // Handle both old format (string[]) and new format (SourceRef[])
          if (Array.isArray(msg.sources)) {
            const first = msg.sources[0];
            if (first && typeof first === "object" && "fileId" in first) {
              sourcesMap[msg.id] = msg.sources as SourceRef[];
            }
            // Old format (string[]) is ignored — no page numbers available
          }
        }
      }
      setMessageSources(sourcesMap);
      if (session.collectionId) {
        setCollectionId(session.collectionId);
      }
    } catch (error) {
      console.error("Error loading existing messages:", error);
    } finally {
      setLoading(false);
    }
  };

  const chatTransport = useMemo(
    () => new DefaultChatTransport({ api: "/api/chat" }),
    []
  );
  const { sendMessage, status, messages: chatMessages, setMessages } = useChat({
    transport: chatTransport,
    onError: (error) => {
      console.error("Chat error:", error);
      toast.error("Failed to send message: " + error.message);
    },
    onFinish: async ({ message: _finishedMessage }) => {
      // After streaming completes, fetch the session to get structured sources
      const currentSessionId = sessionIdRef.current;
      if (currentSessionId) {
        try {
          // Small delay to ensure server-side onFinish has saved the message
          await new Promise((r) => setTimeout(r, 300));
          const res = await fetch(`/api/chat/sessions/${currentSessionId}`);
          if (res.ok) {
            const session = await res.json();
            const dbMessages = session.messages || [];
            // Match by position — db messages and UI messages are in the same order
            const currentMessages = chatMessagesRef.current;
            const sourcesMap: Record<string, SourceRef[]> = {};
            for (let i = 0; i < dbMessages.length && i < currentMessages.length; i++) {
              const dbMsg = dbMessages[i];
              const uiMsg = currentMessages[i];
              if (dbMsg.role === "assistant" && dbMsg.sources && Array.isArray(dbMsg.sources)) {
                const first = dbMsg.sources[0];
                if (first && typeof first === "object" && "fileId" in first) {
                  sourcesMap[uiMsg.id] = dbMsg.sources as SourceRef[];
                }
              }
            }
            setMessageSources((prev) => ({ ...prev, ...sourcesMap }));
          }
        } catch {
          // Sources may not be available immediately, that's OK
        }
      }
    },
  });

  const messages = chatMessages;
  const chatMessagesRef = useRef(chatMessages);
  chatMessagesRef.current = chatMessages;

  const handleCollectionSelect = useCallback(
    (newCollectionId: string, name?: string) => {
      if (newCollectionId === collectionId) return;
      setCollectionId(newCollectionId);
      if (name) setCollectionName(name);
    },
    [collectionId]
  );

  const handleFileCountChange = useCallback((id: string, count: number) => {
    setCollectionFileCount(count);
  }, []);

  const handleVoiceTranscribed = ({
    text,
    languageCode,
    setInput,
  }: {
    text: string;
    languageCode: string;
    setInput: (value: string) => void;
  }) => {
    if (!collectionId) {
      toast.error("Please select a collection first");
      return;
    }

    setLanguageCode(languageCode);
    setInput(text);
    toast.success("Transcription complete - review and edit before sending");
  };

  const handleSubmit = async (message: PromptInputMessage) => {
    if (!collectionId) {
      toast.error("Please select a collection first");
      return;
    }

    const hasText = Boolean(message.text);
    const hasAttachments = Boolean(message.files?.length);

    if (!(hasText || hasAttachments)) {
      return;
    }

    let currentSessionId = sessionId;

    if (!currentSessionId) {
      try {
        const title = (message.text || "New Chat").substring(0, 50);
        const res = await fetch("/api/chat/sessions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ collectionId, title }),
        });
        if (!res.ok) {
          toast.error("Failed to create chat session");
          return;
        }
        const newSession = await res.json();
        currentSessionId = newSession.id;
        setSessionId(currentSessionId);
        justCreatedSessionRef.current = true;
        window.history.replaceState(null, '', `/org/${orgSlug}/chat/${currentSessionId}`);
      } catch (error) {
        console.error("Error creating session:", error);
        toast.error("Failed to create chat session");
        return;
      }
    }

    sendMessage(
      {
        text: message.text || "Sent with attachments",
        files: message.files,
      },
      {
        body: {
          collectionId,
          sessionId: currentSessionId,
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

  const lastAssistantText = lastAssistantMessage?.parts
    ? extractTextContent(lastAssistantMessage.parts)
    : "";

  return (
    <div className="flex h-[calc(100vh-3.5rem)]">
      {/* Left Panel: Collections & Files */}
      <div className="w-72 shrink-0 border-r bg-background overflow-hidden">
        <CollectionFilesPanel
          orgSlug={orgSlug}
          selectedCollectionId={collectionId}
          onSelectCollection={handleCollectionSelect}
          onFileCountChange={handleFileCountChange}
        />
      </div>

      {/* Right Panel: Chat */}
      <div className="flex flex-1 flex-col min-w-0 overflow-hidden">
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
                    ? chatIdFromUrl
                      ? "Your previous conversation will appear here. Start asking new questions!"
                      : "Start asking questions about your documents or upload files to analyze"
                    : "Select a collection from the left panel to begin chatting"
                }
              />
            ) : (
              messages.map((message) => (
                <div key={message.id}>
                  {message.role === "assistant" &&
                    (() => {
                      const structuredSources = messageSources[message.id];
                      if (!structuredSources || structuredSources.length === 0) return null;
                      return (
                        <Sources className="mb-2">
                          <SourcesTrigger count={structuredSources.length} />
                          {structuredSources.map((src, i) => {
                            const viewerUrl = src.fileId && src.pageNo
                              ? `/viewer?fileId=${src.fileId}&page=${src.pageNo}&name=${encodeURIComponent(src.fileName)}`
                              : null;
                            return (
                              <SourcesContent key={`${message.id}-source-${i}`}>
                                {viewerUrl ? (
                                  <button
                                    type="button"
                                    className="flex items-start gap-2 rounded-md border p-2 text-left hover:bg-accent/50 transition-colors w-full"
                                    onClick={() => window.open(viewerUrl, "_blank")}
                                  >
                                    <FileTextIcon className="h-4 w-4 shrink-0 mt-0.5 text-muted-foreground" />
                                    <div className="flex flex-col gap-0.5 min-w-0 flex-1">
                                      <span className="font-medium text-xs truncate">
                                        {src.fileName || "Document"}
                                      </span>
                                      <span className="text-xs text-muted-foreground truncate">
                                        {src.sectionPath}
                                      </span>
                                    </div>
                                    {src.pageNo && (
                                      <span className="text-[10px] bg-secondary text-secondary-foreground px-1.5 py-0.5 rounded shrink-0">
                                        Page {src.pageNo}
                                      </span>
                                    )}
                                    <ExternalLinkIcon className="h-3 w-3 shrink-0 text-muted-foreground mt-0.5" />
                                  </button>
                                ) : (
                                  <div className="flex items-start gap-2 rounded-md border p-2">
                                    <FileTextIcon className="h-4 w-4 shrink-0 mt-0.5 text-muted-foreground" />
                                    <div className="flex flex-col gap-0.5 min-w-0">
                                      <span className="font-medium text-xs truncate">
                                        {src.fileName || "Document"}
                                      </span>
                                      <span className="text-xs text-muted-foreground truncate">
                                        {src.sectionPath}
                                      </span>
                                    </div>
                                    {src.pageNo && (
                                      <span className="text-[10px] bg-secondary text-secondary-foreground px-1.5 py-0.5 rounded shrink-0">
                                        Page {src.pageNo}
                                      </span>
                                    )}
                                  </div>
                                )}
                              </SourcesContent>
                            );
                          })}
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
                            const isDocImage =
                              message.role === "assistant" &&
                              part.url?.includes("/api/files/") &&
                              part.url?.includes("/images/");
                            if (isDocImage) {
                              return (
                                <DocumentImage
                                  key={`${message.id}-docimg-${i}`}
                                  src={part.url!}
                                  alt={part.filename || "Document image"}
                                />
                              );
                            }
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
        <PromptInputProvider>
          <ChatInput
            collectionId={collectionId}
            collectionFileCount={collectionFileCount}
            status={status}
            languageCode={languageCode}
            lastAssistantText={lastAssistantText}
            onSubmit={handleSubmit}
            onVoiceTranscribed={handleVoiceTranscribed}
          />
        </PromptInputProvider>
      </div>
    </div>
  );
}
