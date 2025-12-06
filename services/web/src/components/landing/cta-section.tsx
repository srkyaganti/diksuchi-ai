import Link from "next/link";
import { Button } from "@/components/ui/button";
import { landingContent } from "@/lib/landing-content";

interface CTASectionProps {
  isAuthenticated?: boolean;
}

export function CTASection({ isAuthenticated = false }: CTASectionProps) {
  const { finalCTA } = landingContent;

  return (
    <section className="w-full py-20 lg:py-32">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Gradient Card */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/10 via-accent/20 to-primary/10 p-8 lg:p-16 text-center">
          {/* Content */}
          <div className="relative z-10 max-w-3xl mx-auto">
            <h2 className="text-3xl md:text-4xl font-semibold mb-4 leading-tight">
              {finalCTA.headline}
            </h2>
            <p className="text-base md:text-lg text-muted-foreground mb-8">
              {finalCTA.subheadline}
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              {isAuthenticated ? (
                <Button asChild size="lg" className="text-base px-8 py-6">
                  <Link href="/chat">{finalCTA.primaryCTA}</Link>
                </Button>
              ) : (
                <Button asChild size="lg" className="text-base px-8 py-6">
                  <Link href={finalCTA.primaryCTALink}>
                    {finalCTA.primaryCTA}
                  </Link>
                </Button>
              )}

              {finalCTA.secondaryCTALink !== "#" && (
                <Button
                  asChild
                  variant="outline"
                  size="lg"
                  className="text-base px-8 py-6"
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
