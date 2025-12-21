import * as Icons from "lucide-react";
import { Check } from "lucide-react";
import { WobbleCard } from "@/components/ui/wobble-card";
import { landingContent } from "@/lib/landing-content";

// Government-standard color scheme: Unified blue
const audienceColors = {
  military: {
    bg: "bg-gradient-to-br from-blue-950 to-blue-900",
    icon: "bg-blue-500/30 text-blue-300",
  },
  contractor: {
    bg: "bg-gradient-to-br from-blue-950 to-blue-900",
    icon: "bg-blue-500/30 text-blue-300",
  },
};

export function AudienceSplit() {
  const { audience } = landingContent;

  const audiences = [
    { ...audience.military, key: "military" },
    { ...audience.contractor, key: "contractor" },
  ];

  return (
    <section className="w-full py-20 lg:py-32 bg-accent/3">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl md:text-4xl font-semibold mb-4 leading-tight">
            Who Benefits Most?
          </h2>
          <p className="text-base md:text-lg text-muted-foreground leading-relaxed">
            Diksuchi is purpose-built for mission-critical operations and high-stakes environments
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
          {audiences.map((aud) => {
            const IconComponent =
              (Icons[aud.icon as keyof typeof Icons] || Icons.Users) as React.ComponentType<{className?: string}>;

            const colors = audienceColors[aud.key as keyof typeof audienceColors] || audienceColors.military;

            return (
              <WobbleCard
                key={aud.key}
                containerClassName={`${colors.bg} min-h-[380px]`}
                className="flex flex-col justify-between"
              >
                {/* Header with Icon and Title */}
                <div>
                  <div className={`w-16 h-16 rounded-xl ${colors.icon} flex items-center justify-center mb-6 transition-transform duration-300 group-hover:scale-110`}>
                    <IconComponent className="h-8 w-8" />
                  </div>
                  <h3 className="text-2xl font-semibold text-white mb-4">
                    {aud.title}
                  </h3>
                </div>

                {/* Benefits List */}
                <ul className="space-y-4">
                  {aud.benefits.map((benefit, index) => (
                    <li key={index} className="flex items-start gap-3">
                      <div className="rounded-full p-1 bg-white/20 mt-0.5">
                        <Check className="h-4 w-4 text-white" />
                      </div>
                      <span className="text-sm text-gray-100 leading-relaxed">
                        {benefit}
                      </span>
                    </li>
                  ))}
                </ul>
              </WobbleCard>
            );
          })}
        </div>
      </div>
    </section>
  );
}
