import type { NextConfig } from "next";
import path from "node:path";

// Server-side only (apps/web/.env.local). Not prefixed with NEXT_PUBLIC_, so it never reaches the browser.
const API_URL = process.env.API_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  // Pin the app root so a stray lockfile higher up the filesystem isn't mistaken for the workspace root.
  outputFileTracingRoot: path.resolve(__dirname),
  // Same-origin API: the browser talks to /api/*, Next proxies to FastAPI (cookies just work, no CORS).
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
  },
  async headers() {
    return [
      {
        // The public chat page is the ONLY page that may be framed by other sites.
        source: "/a/:token*",
        headers: [{ key: "Content-Security-Policy", value: "frame-ancestors *" }],
      },
      {
        source: "/((?!a/).*)",
        headers: [
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Content-Security-Policy", value: "frame-ancestors 'none'" },
        ],
      },
      {
        source: "/widget.js",
        headers: [{ key: "Cache-Control", value: "public, max-age=300" }],
      },
    ];
  },
  experimental: {
    // Let uploads slightly over 10 MB reach the API so it can return a proper PDF_TOO_LARGE error.
    middlewareClientMaxBodySize: "25mb",
  },
};

export default nextConfig;
