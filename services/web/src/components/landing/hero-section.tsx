import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ChevronDown } from "lucide-react";
import { WavyBackground } from "@/components/ui/wavy-background";
import { landingContent } from "@/lib/landing-content";

interface HeroSectionProps {
  isAuthenticated?: boolean;
  onGetStarted?: () => void;
}

export function HeroSection({ isAuthenticated = false, onGetStarted }: HeroSectionProps) {
  const { hero } = landingContent;

  return (
    <WavyBackground
      className="max-w-4xl mx-auto text-center"
      containerClassName="w-full"
      blur={10}
      waveOpacity={0.5}
      backgroundFill={"white"}
      waveWidth={100}
    >
      {/* Headline */}
      <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight mb-6 leading-tight text-black">
        {hero.headline}
      </h1>

      {/* Subheadline */}
      <p className="text-lg md:text-xl text-black mb-8 leading-relaxed max-w-3xl mx-auto">
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
          <ChevronDown className="h-6 w-6 mx-auto text-gray-300" />
        </div>
      </div>
    </WavyBackground>
  );
}
