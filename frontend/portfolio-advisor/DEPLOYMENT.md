# Portfolio Advisor Frontend Deployment Guide

## Overview
This guide covers the deployment process for the Portfolio Advisor frontend application, including environment configuration, API integration, and production setup.

## Prerequisites
- Node.js 18+ installed
- Access to your backend API
- API key for authentication
- Deployment platform account (Vercel, Netlify, etc.)

## Environment Configuration

### 1. Create Environment File
Copy `.env.example` to `.env.local`:
```bash
cp .env.example .env.local
```

### 2. Configure Environment Variables
Edit `.env.local` with your production values:

```env
# Backend API Configuration
BACKEND_URL=https://your-backend-api.com
NEXT_PUBLIC_API_URL=https://your-backend-api.com

# API Authentication
NEXT_PUBLIC_API_KEY=your_production_api_key_here

# Optional Configuration
NEXT_PUBLIC_DEFAULT_USER_NAME=Investor
```

### 3. Security Considerations
⚠️ **Important**: The current implementation exposes the API key to the client. For production:
- Consider implementing OAuth or session-based authentication
- Move sensitive API calls to server-side API routes
- Use environment-specific API keys

## Local Testing with Production API

1. Install dependencies:
```bash
npm install
```

2. Run development server with production API:
```bash
npm run dev
```

3. Test the complete flow:
   - Navigate to `/advisor`
   - Complete the questionnaire
   - Verify portfolio generation
   - Test chat functionality

## Production Deployment

### Vercel Deployment (Recommended)

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Deploy:
```bash
vercel --prod
```

3. Set environment variables in Vercel dashboard:
   - Go to Project Settings → Environment Variables
   - Add all variables from `.env.local`
   - Ensure they're set for Production environment

### Manual Deployment

1. Build the application:
```bash
npm run build
```

2. Test production build locally:
```bash
npm start
```

3. Deploy the `.next` folder to your hosting provider

## API Integration Details

### Endpoints Used
The frontend communicates with these backend endpoints via Next.js API routes:

1. **Generate Portfolio**: `POST /api/generate-portfolio-from-wizard`
   - Payload: User questionnaire answers and profile data
   - Response: Portfolio recommendations with holdings

2. **Portfolio Chat**: `POST /api/portfolio-chat`
   - Payload: Chat messages and conversation context
   - Response: AI assistant response

3. **Update Portfolio**: `POST /api/update-portfolio-from-chat`
   - Payload: Current portfolio and chat history
   - Response: Updated portfolio based on conversation

### API Route Proxy
All API calls go through Next.js API routes (`/app/api/*`) which:
- Add authentication headers
- Handle CORS
- Provide error handling
- Keep backend URL server-side

## Features Checklist

- [x] User profile collection (name, birthday)
- [x] Risk assessment questionnaire
- [x] Portfolio generation from wizard
- [x] Portfolio visualization (donut chart)
- [x] Holdings and sectors views
- [x] Chat interface for portfolio questions
- [x] Real-time portfolio updates from chat
- [x] Responsive design
- [x] Smooth scrolling and animations

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Verify `BACKEND_URL` is correct
   - Check API key is valid
   - Ensure backend is running and accessible

2. **Portfolio Not Generated**
   - Check browser console for errors
   - Verify questionnaire data is complete
   - Check network tab for API response

3. **Chat Not Working**
   - Ensure chat endpoints are configured
   - Check for CORS issues
   - Verify API key permissions

### Debug Mode
Enable debug logging by adding to `.env.local`:
```env
NEXT_PUBLIC_DEBUG=true
```

## Monitoring

### Recommended Services
- **Error Tracking**: Sentry
- **Analytics**: Google Analytics or Plausible
- **Performance**: Vercel Analytics
- **Uptime**: UptimeRobot

### Key Metrics to Track
- Portfolio generation success rate
- Average time to complete questionnaire
- Chat interaction frequency
- API response times
- User drop-off points

## Maintenance

### Regular Updates
1. Update dependencies monthly: `npm update`
2. Review and rotate API keys quarterly
3. Monitor error logs weekly
4. Update portfolio data models as needed

### Backup Procedures
1. Export environment variables
2. Backup custom configurations
3. Document any production hotfixes

## Support

For issues or questions:
1. Check error logs in deployment platform
2. Review API documentation
3. Contact backend team for API issues
4. Submit frontend issues to repository

## Version History
- v1.0.0 - Initial release with core features
- Latest updates in CHANGELOG.md