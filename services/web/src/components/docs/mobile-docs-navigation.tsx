"use client";

import { useState } from 'react';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { IconBook } from '@tabler/icons-react';
import { DocsNavigation } from './docs-navigation';
import type { Heading } from '@/lib/mdx-utils';

export function MobileDocsNavigation({ headings }: { headings: Heading[] }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="lg:hidden fixed bottom-6 right-6 z-50">
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger asChild>
          <Button size="lg" className="rounded-full shadow-lg h-14 w-14 p-0">
            <IconBook className="h-5 w-5" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="w-[280px]">
          <div className="mt-8">
            <DocsNavigation headings={headings} />
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}
