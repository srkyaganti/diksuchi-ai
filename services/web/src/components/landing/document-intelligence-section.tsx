import * as Icons from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { FeatureCard } from "./feature-card";
import { landingContent } from "@/lib/landing-content";

// Example Queries Visual Component
function ExampleQueriesVisual() {
  const { documentIntelligence } = landingContent;

  return (
    <div className="w-full space-y-4">
      {documentIntelligence.exampleQueries.map((example, index) => {
        const IconComponent =
          (Icons[example.icon as keyof typeof Icons] || Icons.MessageCircle) as React.ComponentType<{className?: string}>;

        return (
          <Card
            key={index}
            className="transition-all hover:shadow-md hover:scale-[1.02] cursor-pointer"
          >
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <div className="shrink-0 mt-1">
                  <IconComponent className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <div className="text-xs font-semibold text-muted-foreground mb-1">
                    {example.role}
                  </div>
                  <div className="text-sm">{example.query}</div>
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

export function DocumentIntelligenceSection() {
  const { documentIntelligence } = landingContent;

  return (
    <section className="w-full py-20 lg:py-32 bg-accent/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <FeatureCard
          title={documentIntelligence.headline}
          description={documentIntelligence.body}
          techHint={documentIntelligence.techHint}
          visual={<ExampleQueriesVisual />}
          layout="visual-left"
        />
      </div>
    </section>
  );
}
