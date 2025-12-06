import { Badge } from "@/components/ui/badge";
import { landingContent } from "@/lib/landing-content";

export function TechnologyTrust() {
  const { technology } = landingContent;

  return (
    <section className="w-full py-20 lg:py-32 bg-accent/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto">
          {/* Header */}
          <h2 className="text-3xl md:text-4xl font-semibold mb-4 leading-tight">
            {technology.headline}
          </h2>
          <p className="text-base md:text-lg text-muted-foreground mb-8">
            {technology.subheadline}
          </p>

          {/* Technology Badges */}
          <div className="flex flex-wrap justify-center gap-4">
            {technology.badges.map((badge, index) => (
              <div
                key={index}
                className="group cursor-default"
                title={badge.description}
              >
                <Badge
                  variant="secondary"
                  className="text-sm px-4 py-2 transition-all hover:scale-105"
                >
                  {badge.label}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
