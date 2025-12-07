import type { MDXComponents } from 'mdx/types';
import { Tip } from './Tip';
import { Warning } from './Warning';
import { Info } from './Info';
import { StepGuide } from './StepGuide';
import { FeatureCard } from './FeatureCard';

export function useMDXComponents(components: MDXComponents): MDXComponents {
  return {
    // Override default HTML elements
    h1: ({ children }) => (
      <h1 className="text-4xl font-bold mb-6 mt-12 first:mt-0">
        {children}
      </h1>
    ),
    h2: ({ children }) => (
      <h2 className="text-3xl font-semibold mb-4 mt-10 scroll-mt-20">
        {children}
      </h2>
    ),
    h3: ({ children }) => (
      <h3 className="text-2xl font-semibold mb-3 mt-8">
        {children}
      </h3>
    ),
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
