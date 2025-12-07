import * as Icons from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { landingContent } from "@/lib/landing-content";

export function StatsBar() {
  const { stats } = landingContent;

  return (
    <section className="w-full py-12 border-y bg-accent/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {stats.map((stat, index) => {
            const IconComponent =
              (Icons[stat.icon as keyof typeof Icons] || Icons.Star) as React.ComponentType<{className?: string}>;
            return (
              <div key={index} className="flex flex-col items-center text-center">
                <div className="mb-3">
                  <IconComponent className="h-8 w-8 text-primary" />
                </div>
                <div className="text-2xl font-bold mb-1">{stat.value}</div>
                <div className="text-sm text-muted-foreground">{stat.label}</div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
