/** @type {import('next').NextConfig} */
const isCapacitorBuild = process.env.CAPACITOR_BUILD === "1";

const nextConfig = {
  reactStrictMode: true,
  images: { unoptimized: isCapacitorBuild },
  ...(isCapacitorBuild
    ? {
        // Static export for the Android WebView bundle — no Node server
        // ships inside the app; every page is a pre-rendered client-side
        // React app that talks to the FastAPI backend directly.
        output: "export",
        distDir: "out",
      }
    : {
        async rewrites() {
          const apiUrl = process.env.STROMEX_API_URL || "http://localhost:8000";
          return [{ source: "/backend/:path*", destination: `${apiUrl}/:path*` }];
        },
      }),
};

export default nextConfig;
