import type { NextConfig } from "next";

const nextConfig: NextConfig = {
	output: 'standalone', // Required for Docker deployment
	experimental: {
		proxyClientMaxBodySize: '500mb'
	}
};

export default nextConfig;
