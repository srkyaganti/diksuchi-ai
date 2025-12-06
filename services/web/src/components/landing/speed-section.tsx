import { Card, CardContent } from "@/components/ui/card";
import { Check } from "lucide-react";
import { landingContent } from "@/lib/landing-content";

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

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {speed.metrics.map((metric, index) => (
            <Card key={index} className="text-center">
              <CardContent className="pt-6">
                <div className="text-3xl font-bold text-primary mb-2">
                  {metric.value}
                </div>
                <div className="text-sm text-muted-foreground">
                  {metric.label}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Benefits Split */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
          {/* Military Benefits */}
          <Card>
            <CardContent className="p-6">
              <h3 className="text-xl font-semibold mb-4">
                {speed.military.title}
              </h3>
              <ul className="space-y-3">
                {speed.military.benefits.map((benefit, index) => (
                  <li key={index} className="flex items-start gap-3">
                    <Check className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                    <span className="text-sm text-muted-foreground">
                      {benefit}
                    </span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          {/* Contractor Benefits */}
          <Card>
            <CardContent className="p-6">
              <h3 className="text-xl font-semibold mb-4">
                {speed.contractor.title}
              </h3>
              <ul className="space-y-3">
                {speed.contractor.benefits.map((benefit, index) => (
                  <li key={index} className="flex items-start gap-3">
                    <Check className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                    <span className="text-sm text-muted-foreground">
                      {benefit}
                    </span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}
