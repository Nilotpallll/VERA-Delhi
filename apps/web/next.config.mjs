/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@vera/contracts"],
  env: {
    NEXT_PUBLIC_VERA_API_VERSION: "v1",
    NEXT_PUBLIC_API_URL:
      process.env.NEXT_PUBLIC_API_URL ||
      process.env.NEXT_PUBLIC_VERA_API_URL ||
      (process.env.NODE_ENV === "development" ? "http://localhost:8000" : "https://vera-delhi.onrender.com"),
    NEXT_PUBLIC_VERA_API_URL:
      process.env.NEXT_PUBLIC_VERA_API_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      (process.env.NODE_ENV === "development" ? "http://localhost:8000" : "https://vera-delhi.onrender.com"),
  },
};

export default nextConfig;
