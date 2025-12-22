import * as Icons from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Check } from "lucide-react";
import { FeatureCard } from "@/components/ui/feature-card";
import { landingContent } from "@/lib/landing-content";

// Government-standard color scheme: Unified blue
const securityColors = [
  {
    bg: "bg-gradient-to-br from-blue-950 to-blue-900",
    icon: "bg-blue-500/30 text-blue-300",
  },
  {
    bg: "bg-gradient-to-br from-blue-950 to-blue-900",
    icon: "bg-blue-500/30 text-blue-300",
  },
  {
    bg: "bg-gradient-to-br from-blue-950 to-blue-900",
    icon: "bg-blue-500/30 text-blue-300",
  },
];

export function SecuritySection() {
  const { security } = landingContent;

  return (
    <section className="w-full py-20 lg:py-32" id="security">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl md:text-4xl font-semibold mb-4 leading-tight">
            {security.headline}
          </h2>
          <p className="text-lg md:text-xl text-muted-foreground mb-4">
            {security.subheadline}
          </p>
          <p className="text-base text-muted-foreground leading-relaxed">
            {security.body}
          </p>
          <div className="mt-6">
            <Badge variant="secondary" className="font-mono text-xs">
              {security.techHint}
            </Badge>
          </div>
        </div>

        {/* Security Features with Wobble Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
          {security.features.map((feature, index) => {
            const IconComponent =
              (Icons[feature.icon as keyof typeof Icons] || Icons.Shield) as React.ComponentType<{className?: string}>;

            const colors = securityColors[index] || securityColors[0];

            return (
              <FeatureCard
                key={index}
                containerClassName={`${colors.bg} min-h-[300px]`}
                className="flex flex-col justify-between"
              >
                {/* Icon and Title */}
                <div>
                  <div className={`w-14 h-14 rounded-xl ${colors.icon} flex items-center justify-center mb-6 transition-transform duration-300 group-hover:scale-110`}>
                    <IconComponent className="h-7 w-7" />
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-4">
                    {feature.title}
                  </h3>
                </div>

                {/* Benefits List */}
                <ul className="space-y-3">
                  {feature.benefits.map((benefit, idx) => (
                    <li key={idx} className="flex items-start gap-3">
                      <Check className="h-5 w-5 text-white/80 shrink-0 mt-0.5" />
                      <span className="text-sm text-gray-100 leading-relaxed">
                        {benefit}
                      </span>
                    </li>
                  ))}
                </ul>
              </FeatureCard>
            );
          })}
        </div>
      </div>
    </section>
  );
}
