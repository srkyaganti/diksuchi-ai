"use client";

import { useSession } from "@/lib/auth-client";
import { useRouter } from "next/navigation";
import { useScrollToAnchor } from "@/hooks/use-scroll-to-anchor";
import { NavigationHeader } from "@/components/landing/navigation-header";
import { HeroSection } from "@/components/landing/hero-section";
import { StatsBar } from "@/components/landing/stats-bar";
import { FeaturesWobble } from "@/components/landing/features-wobble";
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
  const { data: session } = useSession();
  const router = useRouter();
  const isAuthenticated = !!session;
  const user = session?.user as any;

  // Enable smooth scroll to anchor links
  useScrollToAnchor();

  const handleGetStarted = () => {
    if (user?.isSuperAdmin) {
      router.push("/admin");
    } else {
      router.push("/select-organization");
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <NavigationHeader isAuthenticated={isAuthenticated} />

      {/* Hero Section */}
      <HeroSection isAuthenticated={isAuthenticated} onGetStarted={handleGetStarted} />

      {/* Stats Bar */}
      <StatsBar />

      {/* Features Showcase with Wobble Cards */}
      <section className="w-full py-20 lg:py-32">
        <FeaturesWobble />
      </section>

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
      <CTASection isAuthenticated={isAuthenticated} onGetStarted={handleGetStarted} />

      {/* Footer */}
      <Footer />
    </div>
  );
}
