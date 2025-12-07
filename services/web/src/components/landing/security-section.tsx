import * as Icons from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Check } from "lucide-react";
import { landingContent } from "@/lib/landing-content";

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

        {/* Security Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
          {security.features.map((feature, index) => {
            const IconComponent =
              (Icons[feature.icon as keyof typeof Icons] || Icons.Shield) as React.ComponentType<{className?: string}>;

            return (
              <Card key={index} className="text-center">
                <CardHeader>
                  <div className="mx-auto mb-4">
                    <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                      <IconComponent className="h-6 w-6 text-primary" />
                    </div>
                  </div>
                  <CardTitle className="text-lg">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-left">
                    {feature.benefits.map((benefit, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        <span className="text-sm text-muted-foreground">
                          {benefit}
                        </span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
}
