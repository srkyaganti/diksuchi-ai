"use client";

import { useEffect, useState } from 'react';
import Link from 'next/link';
import type { Heading } from '@/lib/mdx-utils';

export function DocsNavigation({ headings }: { headings: Heading[] }) {
  const [activeId, setActiveId] = useState<string>('');

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id);
          }
        });
      },
      { rootMargin: '-100px 0px -80% 0px' }
    );

    // Observe all heading elements
    const headingElements = headings.map(h =>
      document.getElementById(h.id)
    ).filter(Boolean) as Element[];

    headingElements.forEach(el => observer.observe(el));

    return () => observer.disconnect();
  }, [headings]);

  // Only show H2 headings in TOC
  const tocHeadings = headings.filter(h => h.level === 2);

  return (
    <nav className="sticky top-20 max-h-[calc(100vh-5rem)] overflow-y-auto pr-4">
      <h4 className="font-semibold mb-4 text-sm uppercase text-muted-foreground">
        On This Page
      </h4>
      <ul className="space-y-2 text-sm">
        {tocHeadings.map((heading) => (
          <li key={heading.id}>
            <Link
              href={`#${heading.id}`}
              className={`block py-1 px-2 rounded transition-colors hover:bg-accent hover:text-accent-foreground ${
                activeId === heading.id
                  ? 'bg-accent text-accent-foreground font-medium'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
              onClick={(e) => {
                e.preventDefault();
                const element = document.getElementById(heading.id);
                if (element) {
                  element.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start',
                  });
                  // Update URL hash
                  window.history.pushState(null, '', `#${heading.id}`);
                }
              }}
            >
              {heading.text}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
