/**
 * Landing Page Content Constants
 * Single source of truth for all landing page copy
 */

export const landingContent = {
  metadata: {
    title: "Diksuchi AI - Next-Generation Intelligence for Defence",
    description:
      "Transform how defence forces and contractors access critical documentation. Voice-enabled, AI-powered document intelligence in 18+ Indian languages.",
    openGraph: {
      title: "Diksuchi AI - Next-Generation Intelligence for Defence",
      description:
        "Voice-enabled document intelligence platform for Indian defence forces and contractors. Speak in your language, get instant answers from technical documentation.",
      type: "website",
    },
  },

  navigation: {
    brand: "Diksuchi AI",
    links: [
      { label: "Features", href: "#features" },
      { label: "Security", href: "#security" },
      { label: "How It Works", href: "#how-it-works" },
    ],
    loginCTA: "Login",
    dashboardCTA: "Go to Dashboard",
  },

  hero: {
    headline: "Next-Generation Intelligence for India's Defence Forces",
    subheadline:
      "Transform how you access, understand, and act on critical documentation. Speak in your language. Get instant answers. Stay mission-ready.",
    primaryCTA: "Start Using Diksuchi",
    secondaryCTA: "See How It Works",
    primaryCTALink: "/login",
    secondaryCTALink: "#features",
  },

  stats: [
    {
      icon: "Languages",
      value: "18+",
      label: "Indian Languages",
    },
    {
      icon: "Shield",
      value: "Military-Grade",
      label: "Security",
    },
    {
      icon: "Server",
      value: "On-Premises",
      label: "Deployment",
    },
    {
      icon: "FileCheck",
      value: "S1000D",
      label: "Compliant",
    },
  ],

  voice: {
    headline: "Speak Your Mission, Get Instant Intelligence",
    body: "Whether you're in the field or the factory floor, access critical information hands-free. Ask questions in Hindi, Tamil, Bengali, or any of 18+ Indian languages. Diksuchi understands you—and responds in your language.",
    benefits: [
      "Hands-free operation in high-pressure situations",
      "Natural conversation, not keyword searches",
      "18+ Indian languages for truly inclusive access",
      "Hear answers read aloud while your hands stay on your work",
    ],
    techHint: "Powered by Whisper & Indic ParlerTTS",
    languages: [
      "Hindi",
      "Tamil",
      "Telugu",
      "Bengali",
      "Marathi",
      "Gujarati",
      "Kannada",
      "Malayalam",
      "Punjabi",
      "Odia",
      "Assamese",
      "English",
    ],
  },

  documentIntelligence: {
    headline: "Every Technical Manual. Every Specification. Instantly Searchable.",
    body: "No more hunting through hundreds of pages or endless PDFs. Diksuchi reads and understands S1000D documentation, technical specifications, and maintenance manuals. Ask a question in plain language, get the exact information you need—with source references you can verify.",
    techHint: "Hybrid Retrieval: Vector + Keyword + Knowledge Graph",
    exampleQueries: [
      {
        role: "Pilot",
        icon: "Plane",
        query: "What's the pre-flight hydraulic system check procedure?",
      },
      {
        role: "Engineer",
        icon: "Wrench",
        query: "Show me torque specifications for main wing attachment bolts",
      },
      {
        role: "Contractor",
        icon: "Building2",
        query: "List all components requiring titanium alloy grade 5",
      },
    ],
  },

  security: {
    headline: "Your Intelligence Stays Your Intelligence",
    subheadline: "Built for sovereignty, designed for security",
    body: "Diksuchi runs entirely on your infrastructure. No cloud uploads. No external API calls. No data leaving your secure network. Your sensitive documentation stays exactly where it belongs—under your control.",
    techHint: "PostgreSQL • ChromaDB • Local AI Models",
    features: [
      {
        title: "On-Premises Deployment",
        icon: "Server",
        benefits: [
          "Complete control over your data",
          "Air-gapped environment ready",
          "No internet dependency for operations",
        ],
      },
      {
        title: "Multi-Tenant Architecture",
        icon: "Building",
        benefits: [
          "Secure isolation between units and departments",
          "Role-based access control",
          "Audit trails for compliance",
        ],
      },
      {
        title: "Defence Standards",
        icon: "ShieldCheck",
        benefits: [
          "S1000D technical documentation support",
          "Military-specification infrastructure",
          "Compliance-ready from day one",
        ],
      },
    ],
  },

  speed: {
    headline: "From Hours to Seconds. From Search to Solutions.",
    body: "Stop wasting valuable time hunting through documentation. Diksuchi delivers instant, accurate answers so your teams can focus on what truly matters—mission success and on-time delivery.",
    metrics: [
      {
        value: "95%",
        label: "Reduction in documentation search time",
      },
      {
        value: "2h → 10s",
        label: "Time per technical query",
      },
      {
        value: "50+",
        label: "Questions answered per user per day",
      },
      {
        value: "60%",
        label: "Faster engineering review cycles",
      },
    ],
    military: {
      title: "For Defence Personnel",
      benefits: [
        "Complete pre-flight checks in 15 minutes instead of 45",
        "Faster mission briefings with instant technical data access",
        "Reduced training time for complex systems",
        "Get maintenance answers without leaving the hangar",
      ],
    },
    contractor: {
      title: "For Defence Contractors",
      benefits: [
        "Accelerate bid proposals with rapid specification lookup",
        "Reduce engineering review cycles by 60%",
        "Onboard new team members 3x faster",
        "Improve cross-functional collaboration",
      ],
    },
  },

  howItWorks: {
    headline: "From Upload to Answers in Four Simple Steps",
    steps: [
      {
        number: 1,
        title: "Upload Your Documents",
        description:
          "Add technical manuals, specifications, maintenance guides, and documentation",
        icon: "Upload",
      },
      {
        number: 2,
        title: "Automatic Processing",
        description:
          "Diksuchi analyzes and understands your documents' structure and content",
        icon: "Brain",
        badge: "Vector + Keyword + Graph indexing",
      },
      {
        number: 3,
        title: "Ask Questions",
        description:
          "Use voice or text in any of 18+ Indian languages to query your knowledge base",
        icon: "MessageCircle",
      },
      {
        number: 4,
        title: "Get Instant Answers",
        description:
          "Receive accurate responses with source citations you can verify",
        icon: "CheckCircle",
      },
    ],
  },

  demo: {
    headline: "See Diksuchi in Action",
    description:
      "Experience how Diksuchi transforms complex technical documentation into conversational intelligence.",
    placeholderText:
      "Demo screenshots or video coming soon. Contact us for a live demonstration.",
  },

  audience: {
    military: {
      title: "Built for Mission-Critical Operations",
      icon: "Shield",
      benefits: [
        "Faster decision-making in high-pressure situations",
        "Reduced training time for complex technical systems",
        "Enhanced operational readiness across units",
        "Multi-language support for diverse personnel",
        "Hands-free operation for field use",
      ],
    },
    contractor: {
      title: "Accelerate Your Defence Contracts",
      icon: "Building2",
      benefits: [
        "Rapid compliance verification and documentation",
        "Faster bid preparation and proposal development",
        "Streamlined engineering reviews and approvals",
        "Improved collaboration across distributed teams",
        "Reduced onboarding time for new engineers",
      ],
    },
  },

  technology: {
    headline: "Powered by Battle-Tested Technology",
    subheadline: "Open standards, proven AI, secure infrastructure",
    badges: [
      {
        label: "S1000D Standard",
        description: "Defence technical documentation standard",
      },
      {
        label: "PostgreSQL",
        description: "Enterprise-grade database",
      },
      {
        label: "Whisper AI",
        description: "OpenAI's speech recognition",
      },
      {
        label: "Local AI Models",
        description: "No cloud dependency",
      },
    ],
  },

  finalCTA: {
    headline: "Ready to Transform Your Intelligence Operations?",
    subheadline:
      "Join defence organizations already using Diksuchi to work smarter, faster, and more securely.",
    primaryCTA: "Login to Dashboard",
    secondaryCTA: "View Documentation",
    primaryCTALink: "/login",
    secondaryCTALink: "#", // Update with docs link when available
  },

  footer: {
    brand: "Diksuchi AI",
    tagline: "Next-Generation Intelligence for Defence",
    columns: [
      {
        title: "Product",
        links: [
          { label: "Features", href: "#features" },
          { label: "Security", href: "#security" },
          { label: "How It Works", href: "#how-it-works" },
        ],
      },
      {
        title: "Resources",
        links: [
          { label: "Documentation", href: "#" },
          { label: "Support", href: "#" },
          { label: "API Reference", href: "#" },
        ],
      },
      {
        title: "Legal",
        links: [
          { label: "Privacy Policy", href: "#" },
          { label: "Terms of Service", href: "#" },
          { label: "Compliance", href: "#" },
        ],
      },
      {
        title: "Contact",
        links: [
          { label: "Support", href: "mailto:support@diksuchi.ai" },
          { label: "GitHub", href: "#" },
        ],
      },
    ],
    copyright: `© ${new Date().getFullYear()} Diksuchi AI. All rights reserved.`,
  },
};

export type LandingContent = typeof landingContent;
