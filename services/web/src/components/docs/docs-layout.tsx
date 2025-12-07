"use client";

import { DocsNavigation } from './docs-navigation';
import { MobileDocsNavigation } from './mobile-docs-navigation';
import { NavigationHeader } from '@/components/landing/navigation-header';
import { Footer } from '@/components/landing/footer';
import type { Heading } from '@/lib/mdx-utils';

export function DocsLayout({
  children,
  headings,
}: {
  children: React.ReactNode;
  headings: Heading[];
}) {
  return (
    <div className="min-h-screen bg-background">
      <NavigationHeader />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold mb-4">Diksuchi AI Documentation</h1>
          <p className="text-xl text-muted-foreground">
            Complete guide to using all platform features
          </p>
        </div>

        {/* Desktop: Side-by-side, Mobile: Stacked */}
        <div className="grid lg:grid-cols-[280px_1fr] gap-8">
          {/* Sticky TOC - Hidden on mobile */}
          <aside className="hidden lg:block">
            <DocsNavigation headings={headings} />
          </aside>

          {/* MDX Content */}
          <main className="min-w-0 prose prose-sm sm:prose md:prose-base lg:prose-lg prose-gray dark:prose-invert max-w-none">
            {children}
          </main>
        </div>

        {/* Mobile TOC Button */}
        <MobileDocsNavigation headings={headings} />
      </div>

      <Footer />
    </div>
  );
}
