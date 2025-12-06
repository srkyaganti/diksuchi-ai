import * as Icons from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { landingContent } from "@/lib/landing-content";

export function TimelineSteps() {
  const { howItWorks } = landingContent;

  return (
    <section className="w-full py-20 lg:py-32" id="how-it-works">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl md:text-4xl font-semibold mb-4 leading-tight">
            {howItWorks.headline}
          </h2>
        </div>

        {/* Timeline - Horizontal on desktop, vertical on mobile */}
        <div className="relative">
          {/* Connecting Line - Hidden on mobile */}
          <div className="hidden lg:block absolute top-16 left-0 right-0 h-0.5 bg-border" />

          {/* Steps Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-4">
            {howItWorks.steps.map((step, index) => {
              const IconComponent =
                Icons[step.icon as keyof typeof Icons] || Icons.Circle;

              return (
                <div key={index} className="relative">
                  {/* Step Number Circle */}
                  <div className="relative z-10 w-12 h-12 mx-auto mb-4 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold text-lg">
                    {step.number}
                  </div>

                  {/* Icon */}
                  <div className="flex justify-center mb-4">
                    <div className="w-16 h-16 rounded-lg bg-accent flex items-center justify-center">
                      <IconComponent className="h-8 w-8 text-primary" />
                    </div>
                  </div>

                  {/* Content */}
                  <div className="text-center">
                    <h3 className="text-lg font-semibold mb-2">{step.title}</h3>
                    <p className="text-sm text-muted-foreground mb-3">
                      {step.description}
                    </p>
                    {step.badge && (
                      <Badge variant="outline" className="text-xs font-mono">
                        {step.badge}
                      </Badge>
                    )}
                  </div>

                  {/* Vertical connector for mobile */}
                  {index < howItWorks.steps.length - 1 && (
                    <div className="lg:hidden absolute left-6 top-12 bottom-0 w-0.5 bg-border -mb-8" />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
