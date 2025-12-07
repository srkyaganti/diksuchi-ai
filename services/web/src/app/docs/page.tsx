import { DocsLayout } from '@/components/docs/docs-layout';
import Documentation from '@content/docs/documentation.mdx';
import { extractHeadings } from '@/lib/mdx-utils';
import fs from 'fs';
import path from 'path';

export const metadata = {
  title: 'Diksuchi AI - User Documentation',
  description: 'Complete guide to using Diksuchi AI platform features',
  openGraph: {
    title: 'Diksuchi AI - User Documentation',
    description: 'Complete guide to using Diksuchi AI platform features',
    type: 'website',
  },
};

export default async function DocsPage() {
  // Read MDX file to extract headings for TOC
  const mdxPath = path.join(process.cwd(), 'content/docs/documentation.mdx');
  const mdxContent = fs.readFileSync(mdxPath, 'utf-8');
  const headings = extractHeadings(mdxContent);

  return (
    <DocsLayout headings={headings}>
      <Documentation />
    </DocsLayout>
  );
}
