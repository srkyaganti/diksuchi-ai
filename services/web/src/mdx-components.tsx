import type { MDXComponents } from 'mdx/types';
import GithubSlugger from 'github-slugger';
import { Tip } from './components/docs/Tip';
import { Warning } from './components/docs/Warning';
import { Info } from './components/docs/Info';
import { StepGuide } from './components/docs/StepGuide';
import { FeatureCard } from './components/docs/FeatureCard';

// Create a slugger instance for ID generation
const slugger = new GithubSlugger();

// Helper to extract text from children
function extractText(children: any): string {
  if (typeof children === 'string') return children;
  if (Array.isArray(children)) {
    return children.map(child => extractText(child)).join('');
  }
  if (children?.props?.children) {
    return extractText(children.props.children);
  }
  return '';
}

export function useMDXComponents(components: MDXComponents): MDXComponents {
  return {
    // Override default HTML elements
    h1: ({ children }) => {
      const text = extractText(children);
      const id = text ? slugger.slug(text) : undefined;
      return (
        <h1 id={id} className="text-4xl font-bold mb-6 mt-12 first:mt-0">
          {children}
        </h1>
      );
    },
    h2: ({ children }) => {
      const text = extractText(children);
      const id = text ? slugger.slug(text) : undefined;
      return (
        <h2 id={id} className="text-3xl font-semibold mb-4 mt-10 scroll-mt-20">
          {children}
        </h2>
      );
    },
    h3: ({ children }) => {
      const text = extractText(children);
      const id = text ? slugger.slug(text) : undefined;
      return (
        <h3 id={id} className="text-2xl font-semibold mb-3 mt-8">
          {children}
        </h3>
      );
    },
    p: ({ children }) => (
      <p className="mb-4 leading-7 text-muted-foreground">
        {children}
      </p>
    ),
    ul: ({ children }) => (
      <ul className="list-disc pl-6 mb-4 space-y-2">
        {children}
      </ul>
    ),
    ol: ({ children }) => (
      <ol className="list-decimal pl-6 mb-4 space-y-2">
        {children}
      </ol>
    ),
    code: ({ children }) => (
      <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono">
        {children}
      </code>
    ),
    pre: ({ children }) => (
      <pre className="bg-muted p-4 rounded-lg overflow-x-auto mb-4">
        {children}
      </pre>
    ),

    // Custom components usable in MDX
    Tip,
    Warning,
    Info,
    StepGuide,
    FeatureCard,

    ...components,
  };
}
