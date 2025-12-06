"use client";

import { useSession } from "@/lib/auth-client";
import { NavigationHeader } from "@/components/landing/navigation-header";
import { HeroSection } from "@/components/landing/hero-section";
import { StatsBar } from "@/components/landing/stats-bar";
import { VoiceFeatureSection } from "@/components/landing/voice-feature-section";
import { DocumentIntelligenceSection } from "@/components/landing/document-intelligence-section";
import { SecuritySection } from "@/components/landing/security-section";
import { SpeedSection } from "@/components/landing/speed-section";
import { TimelineSteps } from "@/components/landing/timeline-steps";
import { PlatformDemo } from "@/components/landing/platform-demo";
import { AudienceSplit } from "@/components/landing/audience-split";
import { TechnologyTrust } from "@/components/landing/technology-trust";
import { CTASection } from "@/components/landing/cta-section";
import { Footer } from "@/components/landing/footer";

export default function Home() {
  const { data: session, isPending } = useSession();
  const isAuthenticated = !!session;

  // Show loading state while checking authentication
  if (isPending) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <NavigationHeader isAuthenticated={isAuthenticated} />

      {/* Hero Section */}
      <HeroSection isAuthenticated={isAuthenticated} />

      {/* Stats Bar */}
      <StatsBar />

      {/* Feature Sections */}
      <VoiceFeatureSection />
      <DocumentIntelligenceSection />
      <SecuritySection />
      <SpeedSection />

      {/* How It Works */}
      <TimelineSteps />

      {/* Platform Demo */}
      <PlatformDemo />

      {/* Audience Split */}
      <AudienceSplit />

      {/* Technology Trust */}
      <TechnologyTrust />

      {/* Final CTA */}
      <CTASection isAuthenticated={isAuthenticated} />

      {/* Footer */}
      <Footer />
    </div>
  );
}
