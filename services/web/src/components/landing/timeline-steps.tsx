import * as Icons from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { FeatureCard } from "@/components/ui/feature-card";
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
          <div className="hidden lg:block absolute top-24 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-primary/30 to-transparent" />

          {/* Steps Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-4">
            {howItWorks.steps.map((step, index) => {
              const IconComponent =
                (Icons[step.icon as keyof typeof Icons] || Icons.Circle) as React.ComponentType<{className?: string}>;

              return (
                <div key={index} className="relative">
                  <FeatureCard
                    containerClassName="bg-gradient-to-br from-blue-950 to-blue-900 min-h-[320px]"
                    className="flex flex-col h-full"
                  >
                    <div className="flex flex-col h-full">
                      {/* Step Number Circle */}
                      <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 flex items-center justify-center font-bold text-lg text-white">
                        {step.number}
                      </div>

                      {/* Icon */}
                      <div className="flex justify-center mb-6">
                        <div className="w-16 h-16 rounded-xl bg-blue-500/30 text-blue-300 flex items-center justify-center">
                          <IconComponent className="h-8 w-8" />
                        </div>
                      </div>

                      {/* Content */}
                      <div className="text-center flex-1 flex flex-col">
                        <h3 className="text-lg font-semibold text-white mb-3">
                          {step.title}
                        </h3>
                        <p className="text-sm text-gray-200 mb-4 leading-relaxed flex-1">
                          {step.description}
                        </p>
                        {step.badge && (
                          <Badge variant="secondary" className="text-xs font-mono mx-auto bg-white/10 text-gray-100 border-white/20 hover:bg-white/20">
                            {step.badge}
                          </Badge>
                        )}
                      </div>
                    </div>
                  </FeatureCard>

                  {/* Vertical connector for mobile */}
                  {index < howItWorks.steps.length - 1 && (
                    <div className="lg:hidden absolute left-6 top-32 bottom-0 w-0.5 bg-gradient-to-b from-primary/30 to-transparent -mb-8" />
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
