/** @type {import('next').NextConfig} */
const backendUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL?.trim().replace(/\/$/, '') ||
  'http://localhost:8000'

const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/:path*`,
      },
    ]
  },
}

export default nextConfig
