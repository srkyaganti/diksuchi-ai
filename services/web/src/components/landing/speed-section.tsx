import { Check } from "lucide-react";
import { WobbleCard } from "@/components/ui/wobble-card";
import { landingContent } from "@/lib/landing-content";

// Government-standard color scheme: Unified blue
const speedColors = [
  {
    bg: "bg-gradient-to-br from-blue-950 to-blue-900",
    icon: "bg-blue-500/30 text-blue-300",
  },
  {
    bg: "bg-gradient-to-br from-blue-950 to-blue-900",
    icon: "bg-blue-500/30 text-blue-300",
  },
];

export function SpeedSection() {
  const { speed } = landingContent;

  return (
    <section className="w-full py-20 lg:py-32 bg-accent/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl md:text-4xl font-semibold mb-4 leading-tight">
            {speed.headline}
          </h2>
          <p className="text-base md:text-lg text-muted-foreground leading-relaxed">
            {speed.body}
          </p>
        </div>

        {/* Metrics Grid with Wobble Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {speed.metrics.map((metric, index) => {
            const metricColors = [
              "bg-gradient-to-br from-blue-950 to-blue-900",
              "bg-gradient-to-br from-blue-950 to-blue-900",
              "bg-gradient-to-br from-blue-950 to-blue-900",
              "bg-gradient-to-br from-blue-950 to-blue-900",
            ];

            return (
              <WobbleCard
                key={index}
                containerClassName={`${metricColors[index % metricColors.length]} min-h-[200px]`}
                className="flex flex-col items-center justify-center text-center"
              >
                <div className="text-4xl font-bold text-white mb-3">
                  {metric.value}
                </div>
                <div className="text-sm text-gray-200 leading-relaxed">
                  {metric.label}
                </div>
              </WobbleCard>
            );
          })}
        </div>

        {/* Benefits Split with Wobble Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
          {/* Military Benefits */}
          <WobbleCard
            containerClassName={`${speedColors[0].bg} min-h-[320px]`}
            className="flex flex-col justify-between"
          >
            <div>
              <h3 className="text-xl font-semibold text-white mb-6">
                {speed.military.title}
              </h3>
            </div>
            <ul className="space-y-3">
              {speed.military.benefits.map((benefit, index) => (
                <li key={index} className="flex items-start gap-3">
                  <Check className="h-5 w-5 text-white/80 shrink-0 mt-0.5" />
                  <span className="text-sm text-gray-100">
                    {benefit}
                  </span>
                </li>
              ))}
            </ul>
          </WobbleCard>

          {/* Contractor Benefits */}
          <WobbleCard
            containerClassName={`${speedColors[1].bg} min-h-[320px]`}
            className="flex flex-col justify-between"
          >
            <div>
              <h3 className="text-xl font-semibold text-white mb-6">
                {speed.contractor.title}
              </h3>
            </div>
            <ul className="space-y-3">
              {speed.contractor.benefits.map((benefit, index) => (
                <li key={index} className="flex items-start gap-3">
                  <Check className="h-5 w-5 text-white/80 shrink-0 mt-0.5" />
                  <span className="text-sm text-gray-100">
                    {benefit}
                  </span>
                </li>
              ))}
            </ul>
          </WobbleCard>
        </div>
      </div>
    </section>
  );
}
