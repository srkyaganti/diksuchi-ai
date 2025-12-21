import Link from "next/link";
import { Button } from "@/components/ui/button";
import { landingContent } from "@/lib/landing-content";

interface CTASectionProps {
  isAuthenticated?: boolean;
  onGetStarted?: () => void;
}

export function CTASection({ isAuthenticated = false, onGetStarted }: CTASectionProps) {
  const { finalCTA } = landingContent;

  return (
    <section className="w-full py-20 lg:py-32">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Government-Standard CTA Card */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-950 to-blue-900 border border-blue-800/50 p-8 lg:p-16 text-center transition-all duration-300 hover:shadow-lg hover:border-blue-700/70">
          {/* Animated gradient overlay */}
          <div className="absolute inset-0 opacity-0 hover:opacity-100 transition-opacity duration-300"
            style={{
              background: `radial-gradient(circle at top right, rgba(255,255,255,0.05), transparent)`,
            }}
          />

          {/* Content */}
          <div className="relative z-10 max-w-3xl mx-auto">
            <h2 className="text-3xl md:text-4xl font-semibold mb-4 leading-tight text-white">
              {finalCTA.headline}
            </h2>
            <p className="text-base md:text-lg text-gray-200 mb-8">
              {finalCTA.subheadline}
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              {isAuthenticated ? (
                <Button size="lg" className="text-base px-8 py-6 bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors" onClick={onGetStarted}>
                  {finalCTA.primaryCTA}
                </Button>
              ) : (
                <Button asChild size="lg" className="text-base px-8 py-6 bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors">
                  <Link href={finalCTA.primaryCTALink}>
                    {finalCTA.primaryCTA}
                  </Link>
                </Button>
              )}

              {finalCTA.secondaryCTALink !== "#" && (
                <Button
                  asChild
                  size="lg"
                  className="text-base px-8 py-6 bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors"
                >
                  <Link href={finalCTA.secondaryCTALink}>
                    {finalCTA.secondaryCTA}
                  </Link>
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
