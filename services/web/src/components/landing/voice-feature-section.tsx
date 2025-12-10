import { Badge } from "@/components/ui/badge";
import { FeatureCard } from "./feature-card";
import { landingContent } from "@/lib/landing-content";

// Language Badge Visual Component
function LanguageBadgesVisual() {
  const { voice } = landingContent;

  return (
    <div className="relative w-full h-96 flex items-center justify-center">
      {/* Waveform Background (CSS-based) */}
      <div className="absolute inset-0 flex items-center justify-center gap-1 opacity-20">
        {[...Array(20)].map((_, i) => (
          <div
            key={i}
            className="w-1 bg-primary rounded-full animate-pulse"
            style={{
              height: `${Math.sin(i * 0.5) * 20 + 40}%`,
              animationDelay: `${i * 0.1}s`,
              animationDuration: "1.5s",
            }}
          />
        ))}
      </div>

      {/* Floating Language Badges */}
      <div className="relative grid grid-cols-3 gap-3 md:gap-4">
        {voice.languages.slice(0, 9).map((lang, index) => (
          <Badge
            key={lang}
            variant="outline"
            className="px-3 py-2 text-xs md:text-sm font-medium animate-float"
            style={{
              animationDelay: `${index * 0.2}s`,
              animationDuration: "3s",
            }}
          >
            {lang}
          </Badge>
        ))}
      </div>

      {/* More languages indicator */}
      <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2">
        <Badge variant="secondary" className="text-xs">
          +6 more languages
        </Badge>
      </div>

      <style jsx>{`
        @keyframes float {
          0%,
          100% {
            transform: translateY(0px);
          }
          50% {
            transform: translateY(-10px);
          }
        }
        .animate-float {
          animation: float 3s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}

export function VoiceFeatureSection() {
  const { voice } = landingContent;

  return (
    <section className="w-full py-20 lg:py-32" id="features">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <FeatureCard
          title={voice.headline}
          description={voice.body}
          benefits={voice.benefits}
          techHint={voice.techHint}
          visual={<LanguageBadgesVisual />}
          layout="visual-right"
        />
      </div>
    </section>
  );
}
