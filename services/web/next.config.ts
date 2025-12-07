import type { NextConfig } from "next";
import createMDX from "@next/mdx";

const nextConfig: NextConfig = {
	output: 'standalone', // Required for Docker deployment
	experimental: {
		proxyClientMaxBodySize: '500mb',
	},
	pageExtensions: ['js', 'jsx', 'md', 'mdx', 'ts', 'tsx'],
};

const withMDX = createMDX({
	options: {
		// Use string names for Turbopack compatibility
		remarkPlugins: ['remark-gfm'],
		rehypePlugins: ['rehype-slug'],
	},
});

export default withMDX(nextConfig);
