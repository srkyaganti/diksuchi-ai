import { Card, CardContent } from "@/components/ui/card";
import { landingContent } from "@/lib/landing-content";

export function PlatformDemo() {
  const { demo } = landingContent;

  return (
    <section className="w-full py-20 lg:py-32 bg-accent/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-12">
          <h2 className="text-3xl md:text-4xl font-semibold mb-4 leading-tight">
            {demo.headline}
          </h2>
          <p className="text-base md:text-lg text-muted-foreground">
            {demo.description}
          </p>
        </div>

        {/* Demo Placeholder */}
        <Card className="max-w-5xl mx-auto">
          <CardContent className="p-12 text-center">
            <div className="aspect-video bg-accent/50 rounded-lg flex items-center justify-center">
              <p className="text-muted-foreground max-w-md">
                {demo.placeholderText}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
