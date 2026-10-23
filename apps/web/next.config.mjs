/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@vera/contracts"],
  env: {
    NEXT_PUBLIC_VERA_API_VERSION: "v1",
    NEXT_PUBLIC_API_URL:
      process.env.NEXT_PUBLIC_API_URL ||
      process.env.NEXT_PUBLIC_VERA_API_URL ||
      (process.env.NODE_ENV === "development" ? "http://localhost:8000" : "https://vera-delhi-ldfinal.onrender.com"),
    NEXT_PUBLIC_VERA_API_URL:
      process.env.NEXT_PUBLIC_VERA_API_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      (process.env.NODE_ENV === "development" ? "http://localhost:8000" : "https://vera-delhi-ldfinal.onrender.com"),
  },
  experimental: {
    serverComponentsExternalPackages: ["tesseract.js", "tesseract.js-core"],
    outputFileTracingIncludes: {
      "/api/**/*": [
        "./data/**/*",
        "./apps/web/data/**/*",
        "./eng.traineddata",
        "./apps/web/eng.traineddata",
        "./node_modules/tesseract.js-core/**/*",
        "../../node_modules/tesseract.js-core/**/*",
      ],
    },
  },
};

export default nextConfig;
