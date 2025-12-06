import * as Icons from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Check } from "lucide-react";
import { landingContent } from "@/lib/landing-content";

export function AudienceSplit() {
  const { audience } = landingContent;

  const audiences = [
    { ...audience.military, key: "military" },
    { ...audience.contractor, key: "contractor" },
  ];

  return (
    <section className="w-full py-20 lg:py-32">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
          {audiences.map((aud) => {
            const IconComponent =
              Icons[aud.icon as keyof typeof Icons] || Icons.Users;

            return (
              <Card
                key={aud.key}
                className="border-2 hover:shadow-lg transition-shadow"
              >
                <CardHeader>
                  <div className="mb-4">
                    <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                      <IconComponent className="h-6 w-6 text-primary" />
                    </div>
                  </div>
                  <CardTitle className="text-2xl">{aud.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3">
                    {aud.benefits.map((benefit, index) => (
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
            );
          })}
        </div>
      </div>
    </section>
  );
}
