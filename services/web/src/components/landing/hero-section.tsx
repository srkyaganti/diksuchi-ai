import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ChevronDown } from "lucide-react";
import { landingContent } from "@/lib/landing-content";

interface HeroSectionProps {
  isAuthenticated?: boolean;
  onGetStarted?: () => void;
}

export function HeroSection({ isAuthenticated = false, onGetStarted }: HeroSectionProps) {
  const { hero } = landingContent;

  return (
    <section className="relative w-full py-20 lg:py-32 overflow-hidden">
      {/* Gradient Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-accent/10 to-background -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-4xl mx-auto">
          {/* Headline */}
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight mb-6 leading-tight">
            {hero.headline}
          </h1>

          {/* Subheadline */}
          <p className="text-lg md:text-xl text-muted-foreground mb-8 leading-relaxed max-w-3xl mx-auto">
            {hero.subheadline}
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            {isAuthenticated ? (
              <Button size="lg" className="text-base px-8 py-6" onClick={onGetStarted}>
                {hero.primaryCTA}
              </Button>
            ) : (
              <Button asChild size="lg" className="text-base px-8 py-6">
                <Link href={hero.primaryCTALink}>{hero.primaryCTA}</Link>
              </Button>
            )}

            <Button
              asChild
              variant="outline"
              size="lg"
              className="text-base px-8 py-6"
            >
              <Link href={hero.secondaryCTALink}>
                {hero.secondaryCTA}
                <ChevronDown className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>

          {/* Optional: Scroll indicator animation */}
          <div className="mt-16 hidden lg:block">
            <div className="animate-bounce">
              <ChevronDown className="h-6 w-6 mx-auto text-muted-foreground" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
