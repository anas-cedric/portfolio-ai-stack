/** @type {import('next').NextConfig} */
const nextConfig = {
  /* config options here */
  reactStrictMode: true,
  swcMinify: true,
  async rewrites() {
    // Only add rewrites if API_URL is configured
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    
    if (!apiUrl) {
      console.log('NEXT_PUBLIC_API_URL not set - skipping API rewrites');
      return [];
    }

    return [
      // Proxy new API routes to Railway backend
      {
        source: '/api/risk/:path*',
        destination: `${apiUrl}/risk/:path*`,
      },
      {
        source: '/api/portfolio/propose',
        destination: `${apiUrl}/portfolio/propose`,
      },
      {
        source: '/api/agreements/:path*',
        destination: `${apiUrl}/agreements/:path*`,
      },
      {
        source: '/api/kyc/:path*',
        destination: `${apiUrl}/kyc/:path*`,
      },
      {
        source: '/api/accounts/:path*',
        destination: `${apiUrl}/accounts/:path*`,
      },
      {
        source: '/api/funding/:path*',
        destination: `${apiUrl}/funding/:path*`,
      },
      {
        source: '/api/orders/:path*',
        destination: `${apiUrl}/orders/:path*`,
      },
      {
        source: '/api/rebalance/:path*',
        destination: `${apiUrl}/rebalance/:path*`,
      },
      {
        source: '/api/explain',
        destination: `${apiUrl}/explain`,
      },
      // Keep your existing API routes (these will continue to work as before)
    ]
  },
};

module.exports = nextConfig; 