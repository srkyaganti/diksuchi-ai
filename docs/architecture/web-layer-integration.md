# Web Layer Integration

> Architecture reference for the Next.js web service and its integration with document processing, LLM chat, and image serving.
> Last updated: 2026-03-13

---

## Overview

The web layer is a **Next.js** application that serves as the primary interface for users. It handles authentication, organization management, file uploads, chat with LLM, and image serving. It integrates with PostgreSQL (via Prisma), Redis, the Python document processing service, Ollama (LLM), and an optional voice service.

---

## System Architecture

```mermaid
flowchart TB
    User([User / Browser])

    subgraph NextJS["Next.js Web Service (:3000)"]
        direction TB
        Pages["Pages & Components"]
        APIRoutes["API Routes"]
        Auth["Better Auth"]
        Prisma["Prisma ORM"]
        DocLoader["Document Loader"]
        PyClient["Python Client"]
        LLMClient["LLM Client (AI SDK)"]
    end

    subgraph External["External Services"]
        PG[(PostgreSQL :5432)]
        Redis[(Redis :6379)]
        Ollama["Ollama LLM :11434"]
        PyAPI["Python API :5001"]
        Voice["Voice Service :8001"]
    end

    subgraph Storage["Shared Volumes"]
        Uploads[("uploads_data")]
        DocStore[("storage_data")]
    end

    User --> Pages
    Pages --> APIRoutes
    APIRoutes --> Auth
    APIRoutes --> Prisma
    APIRoutes --> DocLoader
    APIRoutes --> PyClient
    APIRoutes --> LLMClient
    Prisma --> PG
    PyClient --> PyAPI
    PyAPI --> Redis
    LLMClient --> Ollama
    APIRoutes --> Voice
    APIRoutes -->|Write| Uploads
    DocLoader -->|Read| DocStore
```

---

## API Route Map

```mermaid
flowchart TB
    subgraph Auth["/api/auth"]
        AuthAll["[...all] — Better Auth catch-all"]
    end

    subgraph Chat["/api/chat"]
        ChatPost["POST — Send message, stream LLM response"]
        Sessions["GET /sessions — List sessions"]
        SessionsPost["POST /sessions — Create session"]
        SessionID["GET|DELETE /sessions/[id]"]
    end

    subgraph Files["/api/files"]
        FilesPost["POST — Upload file"]
        FileID["GET|DELETE /[id]"]
        Download["GET /[id]/download"]
        Images["GET /[id]/images/[filename]"]
    end

    subgraph Collections["/api/collections"]
        CollList["GET — List collections"]
        CollCreate["POST — Create collection"]
        CollID["GET|PUT|DELETE /[id]"]
        CollFiles["GET /[id]/files"]
    end

    subgraph Internal["/api/internal"]
        FileStatus["POST /file-status — Worker callback"]
    end

    subgraph Org["/api/org"]
        OrgSessions["GET /[slug]/chat-sessions"]
    end

    subgraph Admin["/api/admin"]
        AdminOrgs["POST /organizations — Create org"]
        AdminInvite["POST /invite-member"]
    end

    subgraph Other["/api"]
        Orgs["GET /organizations"]
        OrgSwitch["POST /organizations/[id]/switch"]
        OrgMembers["GET /organizations/[id]/members"]
        ChangePW["POST /user/change-password"]
        Transcribe["POST /voice/transcribe"]
        Synthesize["POST /voice/synthesize"]
    end
```

### Route Summary

| Route | Methods | Purpose |
|-------|---------|---------|
| `/api/auth/[...all]` | GET, POST | Authentication (sign-in, sign-up, sign-out, sessions) |
| `/api/chat` | POST | Stream LLM chat response with document context |
| `/api/chat/sessions` | GET, POST | List / create chat sessions |
| `/api/chat/sessions/[id]` | GET, DELETE | Get / delete a chat session |
| `/api/collections` | GET, POST | List / create document collections |
| `/api/collections/[id]` | GET, PUT, DELETE | Manage a collection |
| `/api/collections/[id]/files` | GET | List files in a collection |
| `/api/files` | POST | Upload a file and trigger processing |
| `/api/files/[id]` | GET, DELETE | File metadata / deletion |
| `/api/files/[id]/download` | GET | Download original uploaded file |
| `/api/files/[id]/images/[filename]` | GET | Serve extracted document images |
| `/api/internal/file-status` | POST, GET | Worker status callback (internal) |
| `/api/organizations` | GET | List organizations |
| `/api/organizations/[id]/switch` | POST | Switch active organization |
| `/api/organizations/[id]/members` | GET | List organization members |
| `/api/org/[slug]/chat-sessions` | GET | List chat sessions for an org |
| `/api/admin/organizations` | POST | Create organization (super admin) |
| `/api/admin/invite-member` | POST | Invite member to organization |
| `/api/user/change-password` | POST | Change user password |
| `/api/voice/transcribe` | POST | Speech-to-text via Voice Service |
| `/api/voice/synthesize` | POST | Text-to-speech via Voice Service |

---

## Chat Flow (Long-Context Approach)

This is the core workflow — how a user question becomes an LLM answer with full document context.

```mermaid
sequenceDiagram
    participant User
    participant UI as Chat UI (useChat)
    participant Chat as POST /api/chat
    participant Auth as Better Auth
    participant DB as PostgreSQL
    participant Loader as document-loader.ts
    participant Disk as storage_data volume
    participant LLM as Ollama LLM

    User->>UI: Types question
    UI->>Chat: POST {messages, collectionId, sessionId}
    Chat->>Auth: Verify session
    Auth-->>Chat: Session + User + Org

    Chat->>DB: Validate collection belongs to org
    Chat->>DB: Find or create ChatSession

    Chat->>Loader: loadCollectionDocuments(collectionId)
    Loader->>DB: Query files WHERE collectionId AND ragStatus = completed
    DB-->>Loader: File records [{id, uuid, name}]

    loop For each file
        Loader->>Disk: Read storage/{uuid}/document.json
        Disk-->>Loader: Docling JSON
        Loader->>Loader: extractTextContent(json)
        Loader->>Loader: extractImageReferences(json)
    end

    Loader-->>Chat: DocumentContent[] {fileName, fileId, textContent, imageRefs}

    Chat->>Chat: buildSystemPrompt(documents)
    Note over Chat: System prompt includes:<br/>• Full text of all documents<br/>• Image URLs: /api/files/{id}/images/{name}<br/>• Instructions for markdown image syntax

    Chat->>LLM: streamText({system, messages, model, temperature: 0.0})
    LLM-->>Chat: Streaming response
    Chat-->>UI: Stream chunks
    UI-->>User: Rendered response with markdown + images

    Chat->>DB: Save user message
    Chat->>DB: Save assistant message with sources
```

### System Prompt Structure

The system prompt injects all document content and image references:

```
You are a technical assistant with access to the following documents...

=== DOCUMENT 1: manual.pdf ===

[Full extracted text content including tables rendered as markdown]

Available images in this document:
- picture_1.png (URL: /api/files/abc123/images/picture_1.png) -- Hydraulic pump assembly (page 47)
- table_1.png (URL: /api/files/abc123/images/table_1.png) (page 12)

=== DOCUMENT 2: spec.pdf ===
...

When referencing an image, use markdown image syntax:
![Description](/api/files/FILEID/images/picture_1.png)
```

---

## File Upload Flow

```mermaid
sequenceDiagram
    participant User
    participant UI as Upload Dialog
    participant API as POST /api/files
    participant Disk as uploads_data
    participant DB as PostgreSQL
    participant PyClient as python-client.ts
    participant PyAPI as Python API (:5001)
    participant Redis

    User->>UI: Select file
    UI->>API: POST multipart/form-data {file, collectionId}
    API->>API: Generate UUID
    API->>Disk: Write uploads/{uuid}.{ext}
    API->>DB: Create File {name, uuid, status: pending, ragStatus: none}
    API->>PyClient: submitDocumentProcessing({fileId, collectionId, fileName, filePath, mimeType, uuid})
    PyClient->>PyAPI: POST /api/process
    PyAPI->>Redis: Enqueue to "document-processing"
    PyAPI-->>PyClient: {jobId, status: queued}
    API-->>UI: 200 File created
    UI-->>User: File appears in list (status: pending)
```

---

## Image Serving Flow

When the LLM references an image in its response, the browser fetches it through this route.

```mermaid
sequenceDiagram
    participant Browser
    participant Route as GET /api/files/[id]/images/[filename]
    participant Auth as Better Auth
    participant DB as PostgreSQL
    participant Disk as storage_data

    Browser->>Route: GET /api/files/abc123/images/picture_1.png
    Route->>Auth: Verify session
    Route->>Route: Validate filename (no path traversal)
    Route->>DB: Find File by id, include Collection
    DB-->>Route: File {uuid, collection.organizationId}
    Route->>Route: Check org authorization
    Route->>Disk: Read storage/{uuid}/images/picture_1.png
    Disk-->>Route: Binary data
    Route-->>Browser: 200 image/png (Cache-Control: immutable, 1 year)
```

### Security Controls

- **Authentication**: Session required via Better Auth.
- **Authorization**: User's active org must match the file's collection org (or super admin).
- **Path traversal**: Filenames containing `..`, `/`, or `\` are rejected.
- **Caching**: Images are immutable — cached for 1 year.

---

## Worker Status Callback Flow

The Python worker notifies Next.js of processing progress through an internal API.

```mermaid
sequenceDiagram
    participant Worker as RQ Worker
    participant API as POST /api/internal/file-status
    participant DB as PostgreSQL

    Worker->>API: POST {fileId, status: processing}<br/>Header: x-api-secret
    API->>API: Validate x-api-secret
    API->>DB: UPDATE File SET ragStatus = processing
    API-->>Worker: 200

    Note over Worker: Docling conversion happens...

    Worker->>API: POST {fileId, status: completed, processedAt}<br/>Header: x-api-secret
    API->>DB: UPDATE File SET ragStatus = completed, processedAt = ...
    API-->>Worker: 200
```

---

## Database Schema (Core Models)

```mermaid
erDiagram
    Organization ||--o{ Collection : has
    Organization ||--o{ ChatSession : has
    Organization ||--o{ Member : has
    User ||--o{ Collection : creates
    User ||--o{ ChatSession : creates
    User ||--o{ Member : belongs_to
    Collection ||--o{ File : contains
    Collection ||--o{ ChatSession : context_for
    ChatSession ||--o{ ChatMessage : contains

    Organization {
        string id PK
        string name
        string slug
        string logo
        string metadata
        datetime createdAt
    }

    Collection {
        string id PK
        string name
        string description
        string organizationId FK
        string userId FK
        datetime createdAt
        datetime updatedAt
    }

    File {
        string id PK
        string name
        string uuid UK
        int fileSize
        string mimeType
        string status
        string collectionId FK
        datetime uploadedAt
        datetime processedAt
        string ragStatus
        string ragError
    }

    ChatSession {
        string id PK
        string organizationId FK
        string collectionId FK
        string userId FK
        string title
        datetime createdAt
        datetime updatedAt
    }

    ChatMessage {
        string id PK
        string sessionId FK
        string role
        string content
        json sources
        datetime createdAt
    }

    User {
        string id PK
        string name
        string email UK
        boolean isSuperAdmin
        boolean mustChangePassword
    }

    Member {
        string id PK
        string organizationId FK
        string userId FK
        string role
    }
```

### Key Fields for Document Pipeline

| Model | Field | Role in Pipeline |
|-------|-------|-----------------|
| `File.uuid` | Maps to `storage/{uuid}/` directory |
| `File.ragStatus` | Tracks processing: `none` → `processing` → `completed` / `failed` |
| `File.ragError` | Stores error message if processing fails |
| `File.processedAt` | Timestamp when Docling conversion completed |
| `Collection.id` | Groups files; used by `loadCollectionDocuments()` to load context |

---

## Frontend Component Architecture

```mermaid
flowchart TB
    subgraph Layout["App Layout"]
        Sidebar["AppSidebar"]
        Navbar["Navbar"]
        OrgSwitcher["OrganizationSwitcher"]
    end

    subgraph ChatPage["Chat Page (/org/[slug]/chat)"]
        ChatUI["Chat Page Component"]
        CollSelector["CollectionSelector"]
        CollFiles["CollectionFilesPanel"]
        PromptInput["PromptInput"]
        VoiceIn["VoiceInput"]
        Conversation["Conversation"]
        Message["Message"]
        Sources["Sources"]
    end

    subgraph DataLib["Data Library (/org/[slug]/data-library)"]
        DLPage["Data Library Page"]
        CollList["Collection List"]
        CreateColl["CreateCollectionDialog"]
        FileList["FileListTable"]
        UploadDlg["FileUploadDialog"]
    end

    subgraph Admin["Admin (/admin)"]
        AdminPage["Admin Dashboard"]
        UserMgmt["User Management"]
        OrgMgmt["Organization Management"]
    end

    Layout --> ChatPage
    Layout --> DataLib
    Layout --> Admin

    ChatUI --> CollSelector
    ChatUI --> CollFiles
    ChatUI --> PromptInput
    ChatUI --> VoiceIn
    ChatUI --> Conversation
    Conversation --> Message
    Message --> Sources
```

### Chat UI Data Flow

```mermaid
flowchart LR
    useChat["useChat hook<br/>(AI SDK)"]
    Transport["DefaultChatTransport<br/>api: /api/chat"]
    Stream["SSE Stream"]

    CollSelector -->|collectionId| useChat
    PromptInput -->|message text| useChat
    VoiceIn -->|transcribed text| useChat
    useChat --> Transport
    Transport -->|POST| Stream
    Stream -->|chunks| Conversation
```

---

## Authentication & Authorization

```mermaid
flowchart TB
    subgraph Auth["Better Auth"]
        EmailPW["Email + Password"]
        Sessions["Session Management<br/>7-day expiry, 1-day refresh"]
        OrgPlugin["Organization Plugin"]
        AdminPlugin["Admin Plugin"]
    end

    subgraph Guards["API Guards"]
        SessionCheck["auth.api.getSession()"]
        OrgCheck["activeOrganizationId match"]
        SuperAdmin["isSuperAdmin flag"]
        APISecret["x-api-secret header<br/>(internal routes only)"]
    end

    EmailPW --> Sessions
    Sessions --> SessionCheck
    OrgPlugin --> OrgCheck
    AdminPlugin --> SuperAdmin

    SessionCheck -->|All user routes| OrgCheck
    SessionCheck -->|Admin routes| SuperAdmin
    APISecret -->|/api/internal/*| InternalRoutes["Worker callbacks"]
```

### Access Control Matrix

| Route Category | Auth Required | Org Scoped | Super Admin Only |
|---------------|:---:|:---:|:---:|
| `/api/chat` | Yes | Yes | No |
| `/api/files` | Yes | Yes | No |
| `/api/collections` | Yes | Yes | No |
| `/api/files/[id]/images/*` | Yes | Yes | No |
| `/api/organizations` | Yes | — | No (filtered) |
| `/api/admin/*` | Yes | — | Yes |
| `/api/internal/*` | No (API secret) | — | — |

---

## LLM Integration

```mermaid
flowchart LR
    ChatRoute["Chat API Route"]
    AISDK["AI SDK<br/>@ai-sdk/openai-compatible"]
    Ollama["Ollama<br/>:11434/v1"]
    Model["Model<br/>(default: llama3.2:3b)"]

    ChatRoute -->|streamText| AISDK
    AISDK -->|OpenAI-compatible API| Ollama
    Ollama --> Model
```

### Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `LLM_SERVICE_BASE_URL` | `http://localhost:11434/v1` | Ollama endpoint |
| `LLM_MODEL` | `llama3.2:3b` | Default model name |

The LLM receives `temperature: 0.0` for deterministic outputs appropriate for safety-critical technical content.

---

## Voice Integration

```mermaid
flowchart LR
    subgraph Browser
        VoiceIn["VoiceInput Component"]
        VoiceOut["VoiceOutput Component"]
    end

    subgraph NextJS["Next.js API"]
        TransAPI["POST /api/voice/transcribe"]
        SynthAPI["POST /api/voice/synthesize"]
    end

    subgraph VoiceSvc["Voice Service (:8001)"]
        Whisper["Whisper (STT)"]
        TTS["Indic Parler TTS"]
    end

    VoiceIn -->|Audio blob| TransAPI
    TransAPI -->|Forward| Whisper
    Whisper -->|Text| TransAPI
    TransAPI -->|Transcription| VoiceIn

    VoiceOut -->|Text| SynthAPI
    SynthAPI -->|Forward| TTS
    TTS -->|Audio| SynthAPI
    SynthAPI -->|Audio blob| VoiceOut
```

---

## End-to-End Data Flow Summary

```mermaid
flowchart TB
    Upload["1. Upload PDF"]
    Store["2. Save to uploads/{uuid}.ext"]
    Enqueue["3. Enqueue processing job"]
    Convert["4. Docling converts PDF"]
    Persist["5. Store JSON + images in storage/{uuid}/"]
    Callback["6. Mark file as completed"]
    Chat["7. User asks question"]
    Load["8. Load all collection documents from disk"]
    Prompt["9. Build system prompt with full text + image URLs"]
    LLM["10. Stream LLM response"]
    Render["11. Render response with inline images"]
    Serve["12. Browser fetches images via /api/files/[id]/images/[name]"]

    Upload --> Store --> Enqueue --> Convert --> Persist --> Callback
    Chat --> Load --> Prompt --> LLM --> Render --> Serve
    Callback -.->|ragStatus: completed| Load
    Persist -.->|storage/{uuid}/| Serve
```
