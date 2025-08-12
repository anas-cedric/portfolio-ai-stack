/** @type {import('next').NextConfig} */
const nextConfig = {
  /* config options here */
  reactStrictMode: true,
  swcMinify: true,
  async rewrites() {
    return [
      // Proxy new API routes to Railway backend
      {
        source: '/api/risk/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/risk/:path*`,
      },
      {
        source: '/api/portfolio/propose',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/portfolio/propose`,
      },
      {
        source: '/api/agreements/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/agreements/:path*`,
      },
      {
        source: '/api/kyc/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/kyc/:path*`,
      },
      {
        source: '/api/accounts/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/accounts/:path*`,
      },
      {
        source: '/api/funding/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/funding/:path*`,
      },
      {
        source: '/api/orders/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/orders/:path*`,
      },
      {
        source: '/api/rebalance/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/rebalance/:path*`,
      },
      {
        source: '/api/explain',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/explain`,
      },
      // Keep your existing API routes (these will continue to work as before)
    ]
  },
};

module.exports = nextConfig; 