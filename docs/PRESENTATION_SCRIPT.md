---
title: "Diksuchi-AI — Presentation Script"
subtitle: "Slide-by-slide breakdown for the PowerPoint deck"
prepared-by: "Srikar Yaganti, Navmate Private Limited"
date: "2026-05-12"
---

# How to use this document

Each section below corresponds to **one slide**. For every slide you will find:

- **Slide title** — what to put at the top of the slide.
- **On-slide content** — the bullets / graphics / numbers that should actually appear on the slide. Keep these terse on the slide itself; the speaker notes carry the detail.
- **Speaker notes (talking script)** — what you say out loud when that slide is on screen.
- **Visual suggestions** — diagrams, screenshots, or icons that would strengthen the slide.

Total deck length: **18 slides**, designed for a ~20–25 minute presentation with Q&A.

---

# Slide 1 — Title slide

**Slide title:** Diksuchi-AI
**Subtitle:** Voice-first document intelligence for defence and mission-critical environments
**Footer line:** Built by Navmate Private Limited • Make in India

**On-slide content:**
- Product logo / wordmark: *Diksuchi-AI*
- Tagline: *"A smart assistant that has read all your technical manuals."*
- Presenter name, title, date
- Navmate logo (bottom-right)

**Speaker notes:**
> Good [morning/afternoon]. I'm here today to introduce **Diksuchi-AI**, a document-intelligence platform built by Navmate for one specific problem: helping people in the field — technicians, engineers, officers — get answers from thousands of pages of technical documentation, by voice, in their own language, in seconds. Before I dive into the product, let me set the stage with a few words about who we are.

**Visual suggestions:**
- Clean dark background; product wordmark centred.
- Subtle visual reference to defence/maintenance (a stylised compass — *diksuchi* means "compass" in Sanskrit — works well thematically).

---

# Slide 2 — Who we are: Navmate

**Slide title:** Navmate Private Limited
**Subtitle:** Secure AI and Data Systems for Mission-Critical Environments

**On-slide content (3-column layout):**

| What we build | Who we build for | How we build |
|---|---|---|
| Sovereign AI systems | Government & defence | On-premise / air-gapped |
| Controlled data infrastructure | Strategic infrastructure programs | Zero external dependencies |
| Blockchain-backed records | Intelligence & logistics | SOC 2 Type II • Zero-trust |
| High-assurance software | | Make in India |

**Speaker notes:**
> Navmate is an Indian deep-tech company. We design **sovereign AI systems, controlled data infrastructure, and high-assurance software** for sensitive, regulated, and disconnected environments — primarily government, defence, and strategic infrastructure.
>
> Three things define how we build:
> 1. **Deployments are on-premise and air-gap-capable** — nothing leaves the customer's network.
> 2. **No external API dependencies** — every model, every database, every queue runs locally.
> 3. **Built for auditability and accreditation** — SOC 2 Type II, zero-trust controls, immutable audit logs.
>
> Diksuchi-AI is our flagship product in the AI category and what we'll spend the rest of this session on.

**Visual suggestions:**
- Navmate logo top-left.
- Four mission-area icons: Intelligence • Defence Operations • Logistics & Asset Integrity • Strategic Infrastructure.
- A small "Made in India" emblem.

---

# Slide 3 — The problem

**Slide title:** A torque value can be 40 pages deep in a 2,000-page manual

**On-slide content:**
- Three pain-points, each with an icon:
  - **Time-consuming** — flipping through dozens of PDFs to find one specification
  - **Error-prone** — risk of citing the wrong revision or wrong procedure
  - **Language barrier** — manuals are in English; technicians may be more fluent in Hindi, Tamil, Telugu, or Hebrew
- A stat-style line: *"Thousands of pages. Dozens of manuals. One technician, one question, one minute to find the answer."*

**Speaker notes:**
> Picture a technician on a maintenance bay. The engine is open. They need one torque value — say, the rear-mount bolt for a specific compressor. That value lives in a 2,000-page manual, possibly in the wrong volume, possibly in a sub-section they have to cross-reference against a separate inspection schedule.
>
> Today the options are: flip pages, use Ctrl-F on a PDF that may or may not be searchable, or call a senior. All three are slow, all three are error-prone, and none of them work if the manual is in English and the technician thinks in Tamil.
>
> Diksuchi-AI exists to compress that loop from minutes to seconds, safely.

**Visual suggestions:**
- A photo of a stack of paper manuals or a cluttered PDF, faded into the background.
- The three pain-points as cards stacked diagonally.

---

# Slide 4 — Introducing Diksuchi-AI

**Slide title:** Diksuchi-AI — Ask your manuals, by voice, in your language

**On-slide content (one-liner + four pillars):**

> *Upload your manuals. Ask in any of 19 languages. Get a precise answer with the exact page and the exact diagram.*

Four pillars:
1. **Voice-first** — speak in 19 languages, listen back in the same one
2. **Document intelligence** — hybrid RAG with page-accurate citations
3. **Safety-aware** — warnings and cautions surfaced before every procedure
4. **Sovereign deployment** — runs fully on-premise; air-gap capable

**Speaker notes:**
> Diksuchi-AI is a **multi-tenant, voice-enabled document-intelligence platform** purpose-built for technical documentation — defence manuals, S1000D documents, equipment procedures, training material.
>
> A user uploads their manuals once. Then anyone in their organisation can **ask a question by voice or text, in their preferred language, and receive a complete, cited answer in seconds** — including the relevant diagram pulled out of the source PDF and embedded in the reply.
>
> Four pillars hold the product up: voice-first multilingual UX, hybrid retrieval that's accurate enough for safety-critical work, a safety-aware LLM contract, and a deployment model that works on a base with no internet.

**Visual suggestions:**
- Hero screenshot of the chat interface with a Hindi/Tamil question, a streaming reply, an inline figure, and a page citation visible.
- Four pillar icons in a row beneath.

---

# Slide 5 — What the user actually does (live walkthrough)

**Slide title:** From question to answer, in three seconds

**On-slide content — numbered flow (use a horizontal timeline):**

1. **Pick a collection** — e.g. "Engine Maintenance — T-90"
2. **Ask in your language** — type or hold-to-talk: *"इंजन ऑयल बदलने के लिए टॉर्क वैल्यू क्या है?"*
3. **Get a precise answer** — language of your choice, with the warning surfaced first
4. **See the figure** — the relevant diagram is embedded inline
5. **Verify the source** — click the citation; the PDF opens at the exact page
6. **(Optional) Listen back** — TTS replays the answer in the user's language

**Speaker notes:**
> Let me walk you through the actual user journey because every design decision flows from this.
>
> Step one — the user logs in and picks the collection of documents relevant to their task. Collections are how we keep, say, the T-90 manuals separate from the artillery manuals inside the same unit.
>
> Step two — they ask. They can type, or they can hold the mic button and speak. The voice path is critical: when a technician is wearing gloves, holding a torque wrench, or under a vehicle, typing is not an option.
>
> Step three — the answer comes back. Three things to notice: it's in **their** language, it leads with the **warning**, and it gives them the **complete procedure** — not a fragment.
>
> Step four — if there is a figure in the source manual that's relevant, the system pulls it out of the PDF and shows it inline. They don't have to go hunting for "Figure 4-7".
>
> Step five — every claim is cited. One click and the original PDF opens at the exact page so they can verify before they act.
>
> Step six — they can play the answer back as audio in the same language. That matters for hands-busy environments.

**Visual suggestions:**
- A 6-step horizontal timeline with miniature UI screenshots at each step (mic, chat bubble, embedded figure, PDF viewer).

---

# Slide 6 — Multi-language voice (our hardest USP)

**Slide title:** 19 languages, voice in and voice out

**On-slide content:**

- **Languages supported (19):** English, Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Assamese, Nepali, Sanskrit, Bhojpuri, Bodo, Dogri, Odia, Manipuri, **Hebrew**
- **Speech-to-text:** Faster-Whisper large-v3, GPU-accelerated, language auto-detect
- **Text-to-speech:** dual-engine routing
  - Indic Parler-TTS — 18 Indian languages with named speakers per language
  - HebTTS (Interspeech 2024) — Hebrew via AlephBERT tokenisation
- **Cross-language RAG:** speech in any language is translated to English **at the STT stage** for retrieval, then the response is generated and spoken in the user's chosen language

**Speaker notes:**
> This slide is the one I want you to remember. Almost every RAG product on the market is monolingual in practice — English in, English out. Diksuchi-AI was built multilingual from day one because our users are not English-first.
>
> We support **19 languages — 18 Indian languages plus Hebrew** — for both speech-in and speech-out. The reason Hebrew is on this list is that one of our deployment contexts requires it, and we vendored a dedicated Hebrew TTS model (HebTTS from Interspeech 2024) because Indian models don't cover Hebrew phonotactics.
>
> Here's the architecturally interesting part. When a Tamil-speaking technician asks a question, we run their speech through Whisper, **translate it to English at the speech-to-text layer**, and use the English text to search the document index. Why? Because the manuals are in English and the embeddings are tuned for English. We get the best retrieval precision that way. Then the LLM generates the response in Tamil, and our TTS speaks it back in Tamil.
>
> Importantly, we preserve **identifiers** through that translation — NSNs, part numbers, acronyms like RPM or ECM stay intact. That's enforced by the system prompt.

**Visual suggestions:**
- A world-map flourish showing the 19 language codes as flags or labels.
- A small architecture diagram: 🎙️ (Hindi audio) → Whisper → English text → RAG → English answer → LLM (translate to Hindi) → Parler-TTS → 🔊 (Hindi audio).

---

# Slide 7 — Document intelligence: how we actually retrieve

**Slide title:** Hybrid RAG with section-complete answers

**On-slide content (pipeline diagram, left to right):**

PDF upload → **Docling** parsing (text + tables + images + structure) → section-aware chunking → **BGE-M3** embeddings + **BM25S** keyword index + **knowledge graph** → query-time **Reciprocal Rank Fusion** → **BGE Reranker v2-m3** cross-encoder → **section expansion** → cited answer with inline figures

**Speaker notes:**
> Under the hood, retrieval is more sophisticated than a typical vector-only RAG. Three reasons it has to be:
>
> First, technical manuals have **structure** — chapters, sections, warning boxes, parts diagrams. We use Docling, currently the best open-source parser for this kind of document, to preserve that structure. Images are extracted and tied back to their parent section.
>
> Second, **safety-critical retrieval cannot rely on semantic similarity alone**. A user asking "torque value for the engine oil drain plug" needs the right number, not a similar-sounding one. We run **three retrieval paths in parallel** — vector search, BM25 keyword search, and a knowledge graph that captures warnings-to-procedure relationships — and fuse the results with reciprocal rank fusion. Then a **cross-encoder reranker** re-scores the top candidates for precision.
>
> Third, we return **whole sections, not chunks**. If a procedure has 20 steps, the user gets all 20 — not a fragment. That single design decision eliminates a huge class of hallucination and "where did step 12 go?" failures.

**Visual suggestions:**
- A clean horizontal pipeline diagram with the seven stages labelled.
- A small inset showing a chunk vs a section, to make the point visually.

---

# Slide 8 — The safety contract

**Slide title:** Warnings first. Specs exact. Sources cited.

**On-slide content (three rules):**

1. **Warnings before steps** — every WARNING, CAUTION, NOTE from the source must appear before the step it applies to
2. **Exact specifications** — torque values, tolerances, NSNs reproduced byte-for-byte, never paraphrased or rounded
3. **Citations required** — every claim carries a file + section + page reference, clickable through to the original PDF

> *"A defence-grade RAG product cannot afford a confident wrong answer. The system prompt makes safety, not fluency, the first priority."*

**Speaker notes:**
> One of the biggest risks with LLMs in this domain is a fluent, confident, *wrong* answer. Our system prompt — which I won't read out in full — codifies three non-negotiable rules.
>
> **One — warnings come first.** If the manual says "WARNING: bleed pressure before removing the plug," the LLM is required to surface that warning before the step it applies to. Always.
>
> **Two — specifications are exact.** No rounding. No paraphrasing. A torque value of 27.5 Nm is 27.5 Nm. NSNs and part numbers are reproduced character-for-character, even when the rest of the answer is being translated into Hindi.
>
> **Three — every answer is cited.** No bare claims. The user can always click through to the original PDF at the exact page and verify before they act.
>
> Together these three rules turn the LLM from a chat toy into something a safety-conscious organisation can actually rely on.

**Visual suggestions:**
- A screenshot of a chat reply where a yellow ⚠️ WARNING box appears above the procedure steps, with a citation at the bottom.

---

# Slide 9 — Architecture at a glance

**Slide title:** Three services, one stack, fully self-hosted

**On-slide content (architecture diagram):**

```
┌──────────────────────────────────────────────────────┐
│  Browser  ──HTTPS──▶  Web App  (Next.js 16, port 3000) │
└──────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
       ┌────────────┐  ┌────────────┐  ┌────────────────┐
       │ RAG Service│  │   Voice    │  │      LLM       │
       │  FastAPI   │  │  Service   │  │ Ollama (local) │
       │  port 5001 │  │ port 8000  │  │  OpenAI-compat │
       └────────────┘  └────────────┘  └────────────────┘
              │               │
   ┌──────────┼───────────┐   │
   ▼          ▼           ▼   ▼
┌────────┐ ┌────────┐ ┌───────────┐
│Postgres│ │ Redis  │ │ ChromaDB  │
│  16    │ │  8.4   │ │  vectors  │
└────────┘ └────────┘ └───────────┘
```

**Speaker notes:**
> Three application services, three pieces of infrastructure, everything runs on the customer's hardware.
>
> The **Web App** is a Next.js 16 application — that's the only thing the user ever sees. It handles auth, multi-tenancy, the chat UI, the data library, and the admin dashboard.
>
> The **RAG Service** is a Python FastAPI worker that does the heavy lifting: parsing PDFs with Docling, computing embeddings, running retrieval and reranking. It uses Redis Queue for async job processing so document ingestion doesn't block the user.
>
> The **Voice Service** is a separate FastAPI process — Whisper for STT and our dual-engine TTS (Indic Parler + HebTTS) — split out because it needs the GPU and benefits from independent scaling.
>
> Underneath: **PostgreSQL** for relational state, **Redis** for the job queue, **ChromaDB** for vectors, and **Ollama** as a local LLM provider. No cloud APIs in the critical path. No data leaves the box.

**Visual suggestions:**
- A clean architecture diagram (matching the ASCII above but in proper boxes/arrows).
- Small "🏠 on-prem" / "✈️ air-gap capable" badges around the perimeter.

---

# Slide 10 — Tech stack

**Slide title:** Built on production-grade open source

**On-slide content (table):**

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind CSS 4, shadcn/ui, AI SDK 5 |
| **Auth & DB** | Better Auth 1.4, Prisma 6, PostgreSQL 16 |
| **RAG pipeline** | FastAPI, Docling 2.79, BGE-M3 embeddings, BM25S, BGE Reranker v2-m3, ChromaDB, NetworkX |
| **Voice** | Faster-Whisper large-v3 (CTranslate2), Indic Parler-TTS, HebTTS (vendored from slp-rl/HebTTS) |
| **LLM** | Ollama (local) — OpenAI-compatible; swappable for any OpenAI-compatible endpoint |
| **Queue & cache** | Redis 8.4 + RQ |
| **Deployment** | systemd user units (production), Docker Compose (dev), no Kubernetes required |

**Speaker notes:**
> A quick note on the stack. Three principles drove every choice.
>
> First — **open source we can self-host**. Every component on this slide runs offline. No vendor SaaS in the data path.
>
> Second — **best-in-class for the job**, not "popular." Docling is currently the state of the art for technical-PDF parsing. BGE-M3 is the best multilingual embedding model we tested. Whisper large-v3 is the only STT that actually handles Indic languages well.
>
> Third — **operationally simple**. We deploy as native systemd user units, not Kubernetes. For a regulated on-prem deployment, a Kubernetes dependency is a liability, not an asset.

**Visual suggestions:**
- Logos of the major OSS projects (Next.js, Postgres, Redis, ChromaDB, FastAPI, Whisper, HuggingFace) in a tidy grid.

---

# Slide 11 — Multi-tenancy and access control

**Slide title:** Organisations, collections, roles — built in

**On-slide content (3-level diagram):**

```
Organisation  ─────  e.g. "T-90 Maintenance Unit"
   │
   ├── Members (admin / member, invitation-based)
   │
   ├── Collection: "Engine Manuals"   ──▶  Documents, Chats
   ├── Collection: "Hydraulics"       ──▶  Documents, Chats
   └── Collection: "Field Procedures" ──▶  Documents, Chats
```

- **Hard data isolation** between organisations (`organizationId` foreign keys everywhere)
- **Role-based access** — admin (full control), member (use)
- **Invitation flow with email verification** — Better Auth, no public sign-ups
- **Super-admin** for cross-organisation operations and onboarding

**Speaker notes:**
> Diksuchi-AI is multi-tenant from the schema up. The top level is the **Organisation** — think a unit, a base, a contractor team. Inside an organisation you have **Collections** — these are the logical grouping of documents and chats for a particular equipment or task family.
>
> Members of an organisation get role-based access — admins manage users and documents, regular members ask questions and view chats. No one in Organisation A can ever see Organisation B's documents, chats, or even know the other organisation exists. That isolation is enforced at the database level by `organizationId` foreign keys on every relevant table.
>
> Onboarding is invitation-only via Better Auth, with email verification. There is no public sign-up.

**Visual suggestions:**
- The 3-level hierarchy as a clean tree.
- Lock icon on the boundary between organisations.

---

# Slide 12 — Deployment model

**Slide title:** Runs on a laptop. Runs in an air-gapped data centre.

**On-slide content:**

- **Three deployment modes:**
  1. **Single-box on-prem** — one server with a GPU, full stack, ideal for a unit or base
  2. **Cluster on-prem** — web/RAG/voice/Postgres split across hosts for scale
  3. **Air-gapped** — no internet at all; models pre-baked into a deployment bundle

- **What we don't depend on:**
  - No SaaS LLM APIs (OpenAI, Anthropic, Gemini)
  - No managed vector DB
  - No managed auth provider
  - No telemetry to external endpoints

- **Hardware footprint (single-box):** 16 GB RAM • 1× NVIDIA GPU (≥ 8 GB VRAM) • 200 GB storage

**Speaker notes:**
> This slide answers the question every IT and security stakeholder asks first: *what does this depend on?*
>
> The answer is **nothing outside the customer's network**. We do not depend on OpenAI, on Anthropic, on any managed vector database, on any cloud auth provider. The entire stack is open source and self-hosted.
>
> That means we can deploy three ways. On a single beefy box with a GPU for smaller units. In a cluster for larger deployments. Or fully air-gapped, with all model weights baked into a deployment bundle that goes through whatever transfer-airlock the customer uses.
>
> Footprint for the single-box mode is modest — 16 GB of RAM, one GPU with 8 GB of VRAM or more, and a couple of hundred GB of storage. That's a workstation, not a data centre.

**Visual suggestions:**
- Three vertical "deployment cards" with icons (laptop / server-rack / air-gap-shield).
- A "no-cloud" stamp graphic on the air-gap card.

---

# Slide 13 — What makes Diksuchi-AI different

**Slide title:** Ten things you won't find in a generic RAG chatbot

**On-slide content (numbered list, two columns):**

1. **Voice-first** in 19 languages, including Hebrew
2. **Section-complete answers**, not fragments
3. **Hybrid retrieval** — vector + BM25 + knowledge graph
4. **Cross-encoder reranking** for precision
5. **Inline figure embedding** — diagrams pulled from the PDF directly into the reply
6. **Page-exact citations** with click-through PDF viewer
7. **Safety-aware system prompt** — warnings always precede procedures
8. **Identifier preservation** — NSNs, part numbers, acronyms never translated
9. **Multi-tenant from the schema up** — organisation, collection, role-based
10. **Fully self-hosted, air-gap capable** — no cloud dependency

**Speaker notes:**
> If you take one slide as a leave-behind, take this one. These ten capabilities are the gap between a generic ChatGPT-on-your-PDFs demo and a system you can actually deploy in a defence-maintenance context.
>
> I'll call out three that buyers usually under-weight on a first pass. **Number two** — section-complete answers. Returning a fragment of a procedure is dangerous in this domain; we always return the whole section. **Number five** — inline figures. The diagram appears in the chat reply, not as a link the user has to click. For a hands-busy operator that matters. And **number eight** — identifier preservation. When we translate an answer into Hindi, "NSN 5331-99-987-1234" stays exactly as "NSN 5331-99-987-1234". The system prompt enforces it and we have worked examples in there to make the LLM honour it.

**Visual suggestions:**
- A 2-column numbered list with small icons next to each.
- A subtle "Diksuchi-AI vs Generic RAG" comparison strip if space allows.

---

# Slide 14 — Use cases

**Slide title:** Where it pays back, today

**On-slide content (four cards):**

1. **Field maintenance** — technician asks for a torque value or inspection step by voice, gets cited answer + diagram in their language.
2. **Officer briefings** — quickly assemble warnings, procedures and notes across multiple manuals for a planned operation.
3. **Training & onboarding** — new recruits practise on real manuals with an interactive assistant; trainer can review chat history.
4. **Cross-language teams** — Hindi-speaking technician and Gujarati-speaking supervisor query the same English source documents, each in their own language.

**Speaker notes:**
> Four representative use cases.
>
> **One** — the field maintenance loop we've been discussing. This is the highest-frequency, highest-value usage.
>
> **Two** — officers preparing for an operation. Instead of pulling five manuals off a shelf and tabbing through warnings, they can ask: "Surface every warning and tool requirement for these three procedures." The system pulls them in one shot, cited.
>
> **Three** — training. New recruits ask their questions, the trainer can review the full chat history, and the system never gets tired of explaining the same procedure ten different ways.
>
> **Four** — the cross-language case. Same documents, same answers, different languages per user. That's a genuine multiplier in mixed-language teams.

**Visual suggestions:**
- Four use-case cards with photographic or illustrated headers.

---

# Slide 15 — Status, performance, what's tuned

**Slide title:** Production-grade today

**On-slide content (table):**

| Dimension | Current state |
|---|---|
| Document parsing | PDF (Docling) production; S1000D XML parser in place |
| End-to-end latency | Streaming first-token typically < 2 s on single-GPU box |
| STT latency | ~1× real-time on GPU (Whisper large-v3) |
| TTS latency | Sub-second for short replies; streaming chunked |
| Concurrent users | Tested per single-box deployment with multi-user organisations |
| Languages | 19 (18 Indian + Hebrew), single source of truth in `tts/registry.py` |
| Auth | Better Auth, email-verified invites, super-admin role |
| Observability | Structured logs across services, RQ job-status callbacks |

**Speaker notes:**
> Quickly on operational maturity. The product is **production-grade today** — not a prototype. PDF ingestion via Docling is the workhorse; S1000D XML parsing is wired in for technical-documentation customers that use that standard.
>
> Latency-wise, first token is typically under two seconds on a single-GPU deployment, with the rest of the answer streaming after. STT runs roughly at real-time on a GPU, and TTS is sub-second for typical replies, chunked so the audio starts playing while the rest is still being synthesised.
>
> We have structured logging across all three services and the RAG worker emits job-status callbacks that the web app uses to drive live progress indicators for document ingestion.

**Visual suggestions:**
- Simple two-column status table; consider a green-check column on the right edge.

---

# Slide 16 — Roadmap

**Slide title:** Where we're headed in the next two quarters

**On-slide content (timeline):**

- **Next quarter**
  - Full S1000D XML rendering with native section navigation
  - Per-collection access policies (sub-organisation roles)
  - Configurable LLM (swap Ollama for any OpenAI-compatible local model)
  - Continuous-listening voice mode for hands-busy workflows
- **Following quarter**
  - Blockchain-backed audit log (provenance for every answer & every source revision) — leverages Navmate's verifiable-systems work
  - Mobile/ruggedised tablet client
  - Multi-modal queries (photo of a part → identify and look up)
  - Federated retrieval across collections

**Speaker notes:**
> A short roadmap so you can see where this is going.
>
> In the **next quarter** we ship full S1000D rendering — for customers whose manuals are already in that standard, the user experience becomes native. We add finer-grained access control inside an organisation. We make the LLM swappable so customers can plug in their own locally-hosted model. And we add a continuous-listening voice mode for cases where the technician simply cannot touch the device.
>
> In the **quarter after that** we pull in Navmate's verifiable-systems infrastructure to add a tamper-evident audit log — every answer and every source revision is provenance-tracked. We ship a mobile and ruggedised-tablet client. And we add multi-modal queries — point a camera at a part, get the manual section for it.

**Visual suggestions:**
- A two-segment horizontal timeline with deliverables under each.

---

# Slide 17 — Why Navmate, why now

**Slide title:** A sovereign AI stack, built in India, for mission-critical use

**On-slide content (three blocks):**

- **Sovereign by design** — no foreign cloud, no foreign API, no data exfiltration risk
- **Built for the constraints that matter** — air-gap, accreditation, audit, regulated
- **Backed by Navmate's broader stack** — secure data infrastructure, blockchain-backed records, defense-grade compute, voice/command interfaces

> *"We don't adapt a consumer AI product for defence. We build for defence from the schema up."*

**Speaker notes:**
> A closing strategic point. There is no shortage of AI chatbots on the market. There is a serious shortage of AI products that **a regulated, sensitive, sovereign organisation can actually deploy** without compromising on data control, accreditation, or operational independence.
>
> That gap is exactly what Navmate exists to close. Diksuchi-AI is the first product, but it sits inside a broader stack — secure data infrastructure, blockchain-backed record systems, voice and command interfaces, defence-grade compute integration. The same engineering constraints — sovereignty, air-gap, auditability — run through all of it.

**Visual suggestions:**
- Three icon-headed columns.
- Navmate's product-category icons in a faint band along the bottom.

---

# Slide 18 — Call to action

**Slide title:** Let's put your manuals to work

**On-slide content:**

- **Try it** — request a sandbox deployment with a sample manual of your choice
- **Pilot it** — 30-day pilot with one collection on your hardware, no data leaves your network
- **Brief us** — share your environment constraints (air-gap, accreditation tier, language mix); we'll come back with a deployment plan

**Contact:**
- contact@navmate.ai
- navmate.ai

**Speaker notes:**
> Three concrete next steps depending on where you are.
>
> If you're exploring, we can stand up a **sandbox** for you with a manual you choose, so you can feel the user experience first-hand.
>
> If you're ready to validate, we run a **30-day on-prem pilot** with one collection, on your hardware, with no data leaving your network.
>
> If you have constraints we should design around — accreditation tier, language mix, hardware envelope — give us those and we'll come back with a tailored deployment plan.
>
> Thank you. I'm happy to take questions.

**Visual suggestions:**
- Three CTA cards.
- Contact block centred at the bottom with the Navmate logo.

---

# Appendix — speaker-prep cheat sheet

**Numbers you may be asked:**
- 19 languages supported (18 Indian + Hebrew)
- 3 application services (Web / RAG / Voice) + 3 infrastructure components (Postgres / Redis / ChromaDB)
- Whisper large-v3 (STT), BGE-M3 (embeddings), BGE Reranker v2-m3 (reranker), Docling 2.79 (parsing)
- Single-box hardware: 16 GB RAM, ≥ 8 GB VRAM, 200 GB storage
- Auth via Better Auth, ORM via Prisma 6, frontend on Next.js 16 + React 19
- LLM provider: Ollama by default (any OpenAI-compatible endpoint works)

**One-liners to keep ready:**
- *"A smart assistant that has read all your technical manuals."*
- *"Warnings first. Specs exact. Sources cited."*
- *"Runs on a laptop. Runs in an air-gapped data centre."*
- *"We don't adapt a consumer AI product for defence. We build for defence from the schema up."*

**Likely tough questions & answers:**

- **"How do you stop the LLM from making things up?"** — Three layers: (1) hybrid retrieval + cross-encoder reranking gives the LLM tightly-scoped context; (2) the system prompt mandates citation of every claim with file/section/page; (3) we return section-complete context, not fragments, so the LLM is never asked to "fill in the missing steps."
- **"What about updates to manuals?"** — Each document is processed into an immutable ingestion record; re-uploading a new revision creates a new record and the chat surface can be pointed at the current revision per collection. Audit-log support for source-revision provenance is on the roadmap.
- **"Why Ollama instead of a hosted model?"** — Customer environments are sovereign and frequently air-gapped. Ollama is a reasonable default; any OpenAI-compatible local model can be plugged in.
- **"How does it compare to Microsoft Copilot / Google NotebookLM / ChatGPT Enterprise?"** — Those are general-purpose, cloud-hosted, English-first products. Diksuchi-AI is purpose-built for technical-manual workflows, voice-first across 19 languages, runs entirely on-premise, and enforces a safety-aware citation contract that consumer-style RAG products do not.
