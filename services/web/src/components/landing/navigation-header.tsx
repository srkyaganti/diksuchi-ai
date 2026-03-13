"use client";

import Link from "next/link";
import Image from "next/image";
import { Menu, X } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { landingContent } from "@/lib/landing-content";

const scrollToElement = (hash: string) => {
  const element = document.querySelector(hash);
  if (element) {
    element.scrollIntoView({ behavior: "smooth", block: "start" });
  }
};

interface NavigationHeaderProps {
  isAuthenticated?: boolean;
}

export function NavigationHeader({
  isAuthenticated = false,
}: NavigationHeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { navigation } = landingContent;

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo/Brand */}
          <div className="flex items-center">
            <Link href="/" className="flex items-center gap-2">
              <span className="text-xl font-bold">Diksuchi</span>
              <span className="text-muted-foreground text-xl font-light">|</span>
              <Image
                src="/avision_logo.png"
                alt="AVision Systems"
                width={120}
                height={36}
                className="h-8 w-auto object-contain"
                priority
              />
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex md:items-center md:space-x-8">
            {navigation.links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
                onClick={(e) => {
                  if (link.href.startsWith("#")) {
                    e.preventDefault();
                    scrollToElement(link.href);
                    window.history.pushState(null, "", link.href);
                  }
                }}
                {...(link.href === "/docs" && {
                  target: "_blank",
                  rel: "noopener noreferrer",
                })}
              >
                {link.label}
              </Link>
            ))}
          </div>

          {/* CTA Button */}
          <div className="hidden md:flex md:items-center">
            {isAuthenticated ? (
              <Button asChild>
                <Link href="/chat">{navigation.dashboardCTA}</Link>
              </Button>
            ) : (
              <Button asChild>
                <Link href="/login">{navigation.loginCTA}</Link>
              </Button>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="flex md:hidden">
            <button
              type="button"
              className="inline-flex items-center justify-center rounded-md p-2 text-muted-foreground hover:bg-accent hover:text-foreground"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden pb-4">
            <div className="space-y-2 pt-2">
              {navigation.links.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="block rounded-md px-3 py-2 text-base font-medium text-muted-foreground hover:bg-accent hover:text-foreground"
                  onClick={(e) => {
                    if (link.href.startsWith("#")) {
                      e.preventDefault();
                      scrollToElement(link.href);
                      window.history.pushState(null, "", link.href);
                    }
                    setMobileMenuOpen(false);
                  }}
                  {...(link.href === "/docs" && {
                    target: "_blank",
                    rel: "noopener noreferrer",
                  })}
                >
                  {link.label}
                </Link>
              ))}
              <div className="pt-4">
                {isAuthenticated ? (
                  <Button asChild className="w-full">
                    <Link href="/chat">{navigation.dashboardCTA}</Link>
                  </Button>
                ) : (
                  <Button asChild className="w-full">
                    <Link href="/login">{navigation.loginCTA}</Link>
                  </Button>
                )}
              </div>
            </div>
          </div>
        )}
      </nav>
    </header>
  );
}
