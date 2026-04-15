---
title: "Diksuchi-AI Platform — Product Document"
subtitle: "Document Intelligence for Defence Equipment Maintenance"
version: "1.0"
date: "April 2025"
prepared-for: "Avision Team"
prepared-by: "Srikar Yaganti"
classification: "Internal"
---

\newpage

# Table of Contents

1. [Document Information](#1-document-information)
2. [Executive Summary](#2-executive-summary)
3. [What Problem Does Diksuchi-AI Solve?](#3-what-problem-does-diksuchi-ai-solve)
4. [Platform Overview](#4-platform-overview)
5. [Key Features](#5-key-features)
   - 5.1 [Document Upload & Processing](#51-document-upload--processing)
   - 5.2 [Intelligent Chat with Your Documents](#52-intelligent-chat-with-your-documents)
   - 5.3 [Page-Level Citations & PDF Viewer](#53-page-level-citations--pdf-viewer)
   - 5.4 [Document Images in Chat](#54-document-images-in-chat)
   - 5.5 [Voice Input & Output](#55-voice-input--output)
   - 5.6 [Multi-Language Support](#56-multi-language-support)
   - 5.7 [Multi-Tenant Organization Management](#57-multi-tenant-organization-management)
   - 5.8 [Admin Dashboard](#58-admin-dashboard)
6. [How to Use — Step-by-Step Guide](#6-how-to-use--step-by-step-guide)
   - 6.1 [Logging In](#61-logging-in)
   - 6.2 [Selecting Your Organization](#62-selecting-your-organization)
   - 6.3 [Creating a Collection](#63-creating-a-collection)
   - 6.4 [Uploading Documents](#64-uploading-documents)
   - 6.5 [Monitoring Document Processing](#65-monitoring-document-processing)
   - 6.6 [Starting a Chat Session](#66-starting-a-chat-session)
   - 6.7 [Asking Questions](#67-asking-questions)
   - 6.8 [Viewing Citations & Source Documents](#68-viewing-citations--source-documents)
   - 6.9 [Using Voice Input](#69-using-voice-input)
   - 6.10 [Using Voice Output (Text-to-Speech)](#610-using-voice-output-text-to-speech)
   - 6.11 [Viewing Chat History](#611-viewing-chat-history)
   - 6.12 [Managing Members](#612-managing-members)
   - 6.13 [Admin Functions](#613-admin-functions)
7. [User Roles & Permissions](#7-user-roles--permissions)
8. [Supported Document Formats](#8-supported-document-formats)
9. [Supported Languages for Voice](#9-supported-languages-for-voice)
10. [System Requirements](#10-system-requirements)
11. [Accessing the Application](#11-accessing-the-application)
12. [Frequently Asked Questions](#12-frequently-asked-questions)
13. [Glossary](#13-glossary)

\newpage

---

# 1. Document Information

| Field | Value |
|---|---|
| **Document Title** | Diksuchi-AI Platform — Product Document |
| **Version** | 1.0 |
| **Date** | April 2025 |
| **Prepared For** | Avision Team |
| **Prepared By** | Srikar Yaganti |
| **Classification** | Internal Use |
| **Distribution** | Avision Team Members |

---

# 2. Executive Summary

Diksuchi-AI is a **document intelligence platform** built specifically for defence equipment maintenance teams. It allows you to upload technical manuals, maintenance procedures, and equipment documentation, and then **ask questions in natural language** (including by voice) to get accurate, cited answers drawn directly from your documents.

Think of it as a **smart assistant that has read all your technical manuals** and can answer questions about any procedure, specification, or troubleshooting step — complete with page references and source images.

### Who Is It For?

- **Technicians** performing maintenance, repair, and inspection tasks on equipment
- **Engineers** looking up specifications, tolerances, and system descriptions
- **Officers** needing quick access to procedural guidance across multiple manuals
- **Trainers** referencing standard operating procedures

### What Makes It Different from a Search Engine?

Unlike a simple text search, Diksuchi-AI:
- **Understands context** — it comprehends what you are asking, not just matching keywords
- **Provides complete answers** — it synthesizes information from multiple sections and documents
- **Cites sources** — every answer links back to the specific page and section in the original PDF
- **Shows images** — relevant diagrams, schematics, and tables from the source documents appear inline in the answer
- **Speaks your language** — supports voice input and output in 18+ Indian languages

---

# 3. What Problem Does Diksuchi-AI Solve?

### The Challenge

Defence equipment maintenance relies on extensive technical documentation — often running into thousands of pages across dozens of manuals. When a technician on the shop floor needs to know a specific torque value, an inspection procedure, or a troubleshooting step, finding the right information is:

- **Time-consuming**: Flipping through hundreds of pages or PDFs
- **Error-prone**: Risk of referencing outdated or wrong procedures
- **Language-barrier**: Manuals are often in English, but users may be more comfortable in Hindi, Tamil, or other Indian languages

### The Solution

Diksuchi-AI turns your static PDF manuals into an **interactive knowledge base**:

1. **Upload** your technical manuals (PDFs) into organized collections
2. **Ask questions** by typing or speaking in any supported language
3. **Get precise answers** with exact page citations and supporting images
4. **Verify sources** by clicking citations to open the original PDF at the exact page

---

# 4. Platform Overview

Diksuchi-AI is a web-based application accessed through your browser. No software installation is needed on your computer.

### Main Screens

| Screen | Purpose |
|---|---|
| **Landing Page** | Public-facing homepage with product information |
| **Login Page** | Secure authentication with email and password |
| **Organization Selector** | Choose which team/unit's documents to work with |
| **Data Library** | Manage collections and upload documents |
| **Chat Interface** | Ask questions and get AI-powered answers |
| **Chat History** | Browse and resume previous conversations |
| **PDF Viewer** | View source documents with page-level navigation |
| **Admin Dashboard** | Manage users, organizations, and memberships |
| **Settings** | Update profile and change password |

### Navigation Structure

After logging in, you work within an **Organization** (e.g., your unit or team). The left sidebar provides access to:

- **Chat** — The main question-answering interface
- **Data Library** — Where documents are organized and uploaded
- **Chat History** — Past conversations with the AI
- **Members** — People in your organization
- **Settings** — Organization settings

---

# 5. Key Features

## 5.1 Document Upload & Processing

Upload PDF documents (technical manuals, maintenance procedures, schematics) into organized collections. The system automatically:

- Extracts all text, tables, and images from the PDF
- Identifies document structure (chapters, sections, subsections)
- Generates image captions using AI vision
- Builds a searchable index for both keyword and semantic search
- Tracks processing status in real-time (pending → processing → completed)

**Supported formats**: PDF files (the system is optimized for S1000D-compliant defence technical documentation)

## 5.2 Intelligent Chat with Your Documents

The core feature of Diksuchi-AI. Ask questions about your uploaded documents and receive:

- **Accurate answers** drawn only from your uploaded documents (no hallucinated information)
- **Complete procedural details** — the system is designed to give full, verbose answers suitable for hands-on technical work
- **Safety information** — all WARNINGs, CAUTIONs, and NOTEs from the source are preserved and highlighted
- **Multi-step procedures** listed in exact order from the manual
- **Exact specifications** — torque values, pressures, tolerances, part numbers reproduced exactly as written

The system supports **multi-turn conversations**, so you can ask follow-up questions and the AI remembers the context of your previous questions.

## 5.3 Page-Level Citations & PDF Viewer

Every answer includes **source citations** that show:

- Which **document** the answer came from
- Which **section** of the document
- Which **page number** the information is on

Click on any citation to **open the original PDF at that exact page** in a built-in PDF viewer. This allows you to verify the AI's answer against the source material.

## 5.4 Document Images in Chat

When the AI's answer references information that includes diagrams, schematics, or tables, these **images are displayed inline** in the chat response. Each image includes:

- A caption describing what it shows
- Zoom capability (click to expand)
- Source attribution

## 5.5 Voice Input & Output

### Voice Input (Speech-to-Text)

Instead of typing, you can **speak your question** using the microphone button:

1. Select your language from the dropdown (10 languages supported)
2. Click **Record** and speak your question
3. Click **Stop** when done
4. Preview the recording, then click **Transcribe**
5. The transcribed text appears in the input field — review and edit if needed, then send

The system converts your speech to text using an AI speech recognition model, supporting automatic language detection.

### Voice Output (Text-to-Speech)

The AI's text response can be **read aloud** to you:

1. After receiving an answer, click the **Speak** button
2. The system summarizes long answers into key sentences and reads them aloud
3. Audio playback shows progress (sentence X of Y)
4. Click **Stop** at any time to end playback
5. Auto-play mode is available — the answer is read aloud automatically when it arrives

### Why This Matters

- **Hands-free operation**: Technicians with dirty hands or wearing gloves can speak questions and hear answers
- **Accessibility**: Users who prefer spoken communication over reading
- **Multi-lingual**: Ask in Hindi, receive the answer in Hindi (spoken and written)

## 5.6 Multi-Language Support

The platform supports voice interaction in **18+ Indian languages** for text-to-speech, and **10 languages** for speech-to-text, including:

| STT Languages (Input) | TTS Languages (Output) |
|---|---|
| English, Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi | Assamese, Bengali, Bodo, Chhattisgarhi, Dogri, English, Gujarati, Hindi, Kannada, Konkani, Malayalam, Manipuri, Marathi, Nepali, Odia, Punjabi, Sanskrit, Tamil, Telugu |

Each TTS language has multiple **speaker voices** (male and female) for natural-sounding output.

## 5.7 Multi-Tenant Organization Management

Diksuchi-AI supports **multiple organizations** (e.g., different units, teams, or departments) with complete data isolation:

- Each organization has its own **collections**, **documents**, and **chat history**
- Users can belong to multiple organizations and switch between them
- Organization administrators can invite and manage members
- Data is never shared between organizations

## 5.8 Admin Dashboard

Super administrators have access to a dedicated **Admin Dashboard** with:

- **User management**: View all users, see their roles and organization memberships
- **Organization management**: Create new organizations, manage memberships
- **Member invitations**: Invite users to organizations via email
- **Statistics**: User count, organization count

---

# 6. How to Use — Step-by-Step Guide

## 6.1 Logging In

1. Open your web browser and navigate to the application URL (e.g., `http://localhost:3000`)
2. Click **"Get Started"** on the landing page
3. Enter your **email address** and **password**
4. Click **"Sign In"**

> **First-time login**: Your administrator will provide your initial email and password. You may be asked to change your password on first login.

## 6.2 Selecting Your Organization

After logging in, you will see the **Organization Selector** page:

1. You will see a list of organizations you belong to
2. Each organization is shown as a card with its name and logo
3. Click on an organization to enter it
4. Once inside, you can switch organizations using the **organization switcher** in the sidebar or header

> **Note**: If you belong to only one organization, you may be taken directly there after login.

## 6.3 Creating a Collection

Collections are like folders that organize your documents:

1. Navigate to **Data Library** from the sidebar
2. Click the **"Create Collection"** button (top right)
3. Enter a **name** for the collection (e.g., "T-72 Engine Maintenance Manuals")
4. Enter an optional **description**
5. Click **"Create"**

The new collection appears as a card in the Data Library.

## 6.4 Uploading Documents

1. From the Data Library, click on a **collection card** to open it
2. Click the **"Upload Files"** button
3. A file upload dialog appears — click **"Browse files"** or drag and drop PDF files
4. You can select multiple files at once
5. Click **"Upload"** to start the upload

> **Important**: Only PDF files are supported. Each file should be a technical manual or document relevant to the collection's purpose.

## 6.5 Monitoring Document Processing

After uploading, each document goes through a processing pipeline:

1. In the collection view, each file shows a **status badge**:
   - **Pending** (yellow) — Waiting to be processed
   - **Processing** (blue) — Currently being analyzed
   - **Completed** (green) — Ready for querying
   - **Failed** (red) — An error occurred during processing

2. Processing typically takes 1-5 minutes per document depending on size
3. You can refresh the page to see updated status
4. Once a document shows **"Completed"**, it is ready for chat queries

## 6.6 Starting a Chat Session

1. Navigate to **Chat** from the sidebar
2. The left panel shows your collections — select the collection you want to query
3. The chat area opens on the right with an empty conversation
4. You are now ready to ask questions about documents in that collection

> **Note**: You must select a collection before you can start chatting. The chat only answers based on documents in the selected collection.

## 6.7 Asking Questions

Type your question in the input field at the bottom and press **Enter** or click the send button.

**Tips for best results:**
- Be specific: "What is the torque specification for the M12 bolts on the cylinder head?" works better than "bolt torque"
- Mention equipment names or part numbers when relevant
- For procedures, ask "How do I..." or "Step-by-step procedure for..."
- For troubleshooting, describe the symptom: "Engine overheating during sustained operation above 2000 RPM"
- For specifications, ask directly: "What is the oil capacity of the T-72 transmission?"

## 6.8 Viewing Citations & Source Documents

After receiving an answer:

1. Look for the **"Sources"** section above the AI's response
2. Click the **"Sources"** button to expand the list of source references
3. Each source shows:
   - **Document name** — Which PDF the information came from
   - **Section path** — The specific section within the document
   - **Page number** — The exact page in the PDF
4. Click on any source reference to **open the PDF viewer** at that exact page
5. In the PDF viewer, you can scroll through the document to see the full context

## 6.9 Using Voice Input

1. In the chat input area, locate the **microphone controls** (below the text input)
2. Select your **language** from the dropdown (default: English)
3. Click the **"Record"** button — the browser will ask for microphone permission (grant it)
4. Speak your question clearly
5. Click **"Stop Recording"** when finished
6. A **preview player** appears — listen to your recording
7. Click **"Transcribe"** to convert speech to text
8. The transcribed text appears in the input field — **review and edit** if needed
9. Press Enter or click Send to submit the question

## 6.10 Using Voice Output (Text-to-Speech)

After receiving an AI response:

1. Locate the **"Speak"** button near the chat input area
2. Click **"Speak"** to have the response read aloud
3. The system will:
   - Summarize long responses into key sentences
   - Generate audio for each sentence
   - Play them in sequence
4. Progress is shown (e.g., "3/8" means sentence 3 of 8)
5. Click **"Stop"** to end playback at any time

> **Auto-play**: If enabled, responses are read aloud automatically as they arrive.

## 6.11 Viewing Chat History

1. Navigate to **Chat History** from the sidebar
2. A table shows all your past conversations with:
   - **Title** — Auto-generated from your first question
   - **Collection** — Which document collection was queried
   - **Date** — When the conversation took place
3. Click on any conversation to **resume** it and continue asking questions

## 6.12 Managing Members

Organization members can view and manage team membership:

1. Navigate to **Members** from the sidebar
2. See a list of all current members with their roles
3. **Admins** can invite new members:
   - Click **"Invite Member"**
   - Enter the email address and select a role
   - The invitation is created in the system

## 6.13 Admin Functions

Super administrators have access to the **Admin Dashboard** at `/admin`:

### Managing Organizations
1. Go to **Admin → Organizations**
2. View all organizations
3. Click **"Create Organization"** to add a new one
4. Enter name and slug (URL-friendly identifier)
5. Click on an organization to manage its members

### Managing Users
1. Go to **Admin → Users**
2. View all registered users
3. See their roles, organization memberships, and status

### Inviting Members to an Organization
1. Go to **Admin → Organizations** → Click on an organization
2. Go to the **Members** tab
3. Click **"Invite Member"**
4. Enter the email and select a role (Admin or Member)
5. The user will appear in the member list

---

# 7. User Roles & Permissions

| Role | Description | Capabilities |
|---|---|---|
| **Super Admin** | Platform administrator | Full access: manage all users, organizations, collections, and chat sessions. Can access the Admin Dashboard. Can chat with any collection. |
| **Organization Admin** | Admin of a specific organization | Can invite/remove members, manage collections and documents within their organization |
| **Organization Member** | Regular user within an organization | Can create collections, upload documents, and chat within their organization |
| **Unaffiliated User** | User not in any organization | Cannot access any collections or chat until added to an organization |

---

# 8. Supported Document Formats

| Format | Support Level | Notes |
|---|---|---|
| **PDF** | Full support | Primary format. Optimized for S1000D defence technical documentation. Text, tables, images, and structure are all extracted. |
| DOCX | Not yet supported | Planned for future release |
| S1000D XML | Not yet supported | Planned for future release |

---

# 9. Supported Languages for Voice

### Speech-to-Text (Input — 10 languages)

| Code | Language |
|---|---|
| en | English |
| hi | Hindi |
| bn | Bengali |
| ta | Tamil |
| te | Telugu |
| mr | Marathi |
| gu | Gujarati |
| kn | Kannada |
| ml | Malayalam |
| pa | Punjabi |

### Text-to-Speech (Output — 18+ languages, multiple voices each)

Assamese, Bengali, Bodo, Chhattisgarhi, Dogri, English, Gujarati, Hindi, Kannada, Konkani, Malayalam, Manipuri, Marathi, Nepali, Odia, Punjabi, Sanskrit, Tamil, Telugu

---

# 10. System Requirements

### For Users (Accessing the Application)

| Requirement | Minimum |
|---|---|
| **Web Browser** | Chrome 90+, Firefox 90+, Edge 90+, or Safari 15+ |
| **Internet/Network** | Access to the server where Diksuchi-AI is hosted |
| **Microphone** | Required for voice input (browser will request permission) |
| **Speakers/Headphones** | Required for voice output |
| **Screen Resolution** | 1280x720 or higher recommended |

### For Server Deployment

| Requirement | Minimum | Recommended |
|---|---|---|
| **RAM** | 16 GB | 32 GB |
| **Disk Space** | 50 GB | 100+ GB |
| **GPU** | NVIDIA GPU with 8 GB+ VRAM | NVIDIA GPU with 16 GB+ VRAM |
| **CPU** | 8 cores | 16+ cores |
| **OS** | Windows with WSL2, or Linux | Linux (Ubuntu 22.04+) |
| **Docker** | Docker Desktop with WSL2 | Docker Engine |

---

# 11. Accessing the Application

| Service | URL | Purpose |
|---|---|---|
| **Web Application** | `http://<server-ip>:3000` | Main user interface |
| **RAG Service** | `http://<server-ip>:5001` | Document processing (internal) |
| **Voice Service** | `http://<server-ip>:8000` | Speech processing (internal) |

> The RAG Service and Voice Service are backend services — users do not need to access them directly.

---

# 12. Frequently Asked Questions

### General

**Q: Does the AI make up answers?**
A: No. The system is designed to answer only from your uploaded documents. If it cannot find relevant information, it will say so. It will never fabricate part numbers, torque values, or procedures.

**Q: Can I ask questions in Hindi or other Indian languages?**
A: Yes. The system responds in the same language you write in. For voice, you can select from 10 input languages and 18+ output languages.

**Q: How many documents can I upload?**
A: There is no hard limit. The system handles collections with many documents. Processing time scales with document size.

**Q: Can I use the system offline?**
A: The system runs on your local server/infrastructure. It does not require an internet connection to function. All data stays within your network.

### Security & Data

**Q: Is my data sent to the cloud?**
A: No. All AI models run locally on your server. No document content or questions are sent to external services.

**Q: Can users in different organizations see each other's documents?**
A: No. Data is completely isolated between organizations. A user in Organization A cannot access any data from Organization B.

**Q: Who can see my chat history?**
A: Chat sessions are visible to the user who created them. Super admins can also access all sessions for administrative purposes.

### Performance

**Q: How long does document processing take?**
A: Typically 1-5 minutes per PDF, depending on size and complexity. Large technical manuals with many images may take longer.

**Q: How fast are chat responses?**
A: Responses are streamed in real-time. The first tokens typically appear within 3-5 seconds, with the full answer completing based on length.

---

# 13. Glossary

| Term | Definition |
|---|---|
| **Collection** | A named group of related documents (like a folder) used for organizing your knowledge base |
| **Chat Session** | A conversation thread where you ask questions and receive AI answers about documents in a specific collection |
| **Citation** | A reference to the specific source (document, section, page) from which an answer was derived |
| **RAG** | Retrieval-Augmented Generation — the AI technique of finding relevant information from documents first, then generating an answer based on that information |
| **Embedding** | A mathematical representation of text that captures its meaning, used for semantic search |
| **BM25** | A keyword search algorithm that ranks documents based on term frequency — like a smart "Ctrl+F" |
| **Reranking** | A second-pass scoring step that refines search results for better accuracy |
| **Hybrid Search** | Combining multiple search methods (semantic + keyword) for more comprehensive results |
| **S1000D** | An international standard for technical documentation, commonly used in defence and aerospace |
| **Tenant/Organization** | A logically separated workspace with its own users, documents, and data — ensuring isolation between different teams or units |
| **Chunk** | A small segment of a document, used for search and retrieval. The system divides documents into chunks to enable precise matching |
| **STT** | Speech-to-Text — converting spoken language into written text |
| **TTS** | Text-to-Speech — converting written text into spoken audio |
| **Vector Database** | A specialized database that stores and searches mathematical representations (embeddings) of text for semantic similarity |

---

*End of Product Document*
