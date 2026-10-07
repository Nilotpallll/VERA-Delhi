/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@vera/contracts"],
  env: {
    NEXT_PUBLIC_VERA_API_VERSION: "v1",
  },
};

export default nextConfig;
