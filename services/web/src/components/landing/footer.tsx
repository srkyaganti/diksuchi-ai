import Link from "next/link";
import { Separator } from "@/components/ui/separator";
import { landingContent } from "@/lib/landing-content";

export function Footer() {
  const { footer } = landingContent;

  return (
    <footer className="w-full border-t bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
        {/* Brand Section */}
        <div className="mb-8">
          <h3 className="text-xl font-bold mb-2">{footer.brand}</h3>
          <p className="text-sm text-muted-foreground">{footer.tagline}</p>
        </div>

        <Separator className="my-8" />

        {/* Footer Links Grid */}
        <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {footer.columns.map((column) => (
            <div key={column.title}>
              <h4 className="text-sm font-semibold mb-4">{column.title}</h4>
              <ul className="space-y-3">
                {column.links.map((link) => (
                  <li key={link.label}>
                    <Link
                      href={link.href}
                      className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <Separator className="my-8" />

        {/* Copyright */}
        <div className="text-center text-sm text-muted-foreground">
          {footer.copyright}
        </div>
      </div>
    </footer>
  );
}
