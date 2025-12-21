import { FeatureCard } from "./feature-card";
import { DocumentIntelligenceCards } from "./document-intelligence-cards";
import { landingContent } from "@/lib/landing-content";

export function DocumentIntelligenceSection() {
  const { documentIntelligence } = landingContent;

  return (
    <section className="w-full py-20 lg:py-32 bg-accent/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="space-y-12">
          {/* Section Header */}
          <div className="max-w-3xl">
            <h2 className="text-3xl md:text-4xl font-semibold mb-4 leading-tight">
              {documentIntelligence.headline}
            </h2>
            <p className="text-base md:text-lg text-muted-foreground mb-6 leading-relaxed">
              {documentIntelligence.body}
            </p>
            {documentIntelligence.techHint && (
              <div className="inline-block px-4 py-2 bg-secondary rounded-lg text-xs font-mono font-medium text-secondary-foreground">
                {documentIntelligence.techHint}
              </div>
            )}
          </div>

          {/* Infinite Moving Cards */}
          <DocumentIntelligenceCards />
        </div>
      </div>
    </section>
  );
}
