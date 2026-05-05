import type { NextConfig } from "next";
import createMDX from "@next/mdx";

const nextConfig: NextConfig = {
	experimental: {
		proxyClientMaxBodySize: '500mb',
	},
	pageExtensions: ['js', 'jsx', 'md', 'mdx', 'ts', 'tsx'],
};

const withMDX = createMDX({
	options: {
		remarkPlugins: ['remark-gfm'],
		rehypePlugins: ['rehype-slug'],
	},
});

export default withMDX(nextConfig);
