import Link from "next/link";
import Image from "next/image";
import { Separator } from "@/components/ui/separator";
import { landingContent } from "@/lib/landing-content";

export function Footer() {
  const { footer } = landingContent;

  return (
    <footer className="w-full border-t bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
        {/* Brand Section */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <h3 className="text-xl font-bold">Diksuchi</h3>
              <span className="text-muted-foreground text-xl font-light">|</span>
              <Image
                src="/avision_logo.png"
                alt="AVision Systems"
                width={120}
                height={36}
                className="h-8 w-auto object-contain"
              />
            </div>
            <p className="text-sm text-muted-foreground">{footer.tagline}</p>
          </div>
          <Image
            src="/make-in-india-logo.png"
            alt="Make in India"
            width={100}
            height={60}
            className="h-14 w-auto object-contain"
          />
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
                      {...(link.href === "/docs" && {
                        target: "_blank",
                        rel: "noopener noreferrer"
                      })}
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
        <div className="flex items-center justify-center gap-4 text-sm text-muted-foreground">
          <span>{footer.copyright}</span>
          <Image
            src="/make-in-india-logo.png"
            alt="Make in India"
            width={60}
            height={36}
            className="h-8 w-auto object-contain"
          />
        </div>
      </div>
    </footer>
  );
}
