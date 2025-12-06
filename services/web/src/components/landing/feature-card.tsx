import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Check } from "lucide-react";

interface FeatureCardProps {
  title: string;
  description: string;
  benefits?: string[];
  techHint?: string;
  visual?: React.ReactNode;
  layout?: "visual-left" | "visual-right";
  className?: string;
}

export function FeatureCard({
  title,
  description,
  benefits,
  techHint,
  visual,
  layout = "visual-right",
  className,
}: FeatureCardProps) {
  const isVisualLeft = layout === "visual-left";

  return (
    <div className={className}>
      <div
        className={`grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-center ${
          isVisualLeft ? "lg:flex-row-reverse" : ""
        }`}
      >
        {/* Content Section */}
        <div className={isVisualLeft ? "lg:col-start-2" : ""}>
          <h2 className="text-3xl md:text-4xl font-semibold mb-4 leading-tight">
            {title}
          </h2>
          <p className="text-base md:text-lg text-muted-foreground mb-6 leading-relaxed">
            {description}
          </p>

          {/* Benefits List */}
          {benefits && benefits.length > 0 && (
            <ul className="space-y-3 mb-6">
              {benefits.map((benefit, index) => (
                <li key={index} className="flex items-start gap-3">
                  <Check className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                  <span className="text-sm md:text-base text-muted-foreground">
                    {benefit}
                  </span>
                </li>
              ))}
            </ul>
          )}

          {/* Tech Hint Badge */}
          {techHint && (
            <Badge variant="secondary" className="font-mono text-xs">
              {techHint}
            </Badge>
          )}
        </div>

        {/* Visual Section */}
        {visual && (
          <div
            className={`${
              isVisualLeft ? "lg:col-start-1 lg:row-start-1" : ""
            } flex items-center justify-center`}
          >
            {visual}
          </div>
        )}
      </div>
    </div>
  );
}
