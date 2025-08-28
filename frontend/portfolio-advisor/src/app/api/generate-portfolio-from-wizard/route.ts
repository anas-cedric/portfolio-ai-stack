import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    // For local development
    const BACKEND_URL = process.env.NODE_ENV === 'development' 
      ? 'http://localhost:8000' 
      : process.env.BACKEND_URL || '';

    // Prevent accidental recursion in production if BACKEND_URL is not set
    if (process.env.NODE_ENV !== 'development' && !BACKEND_URL) {
      return NextResponse.json(
        { error: 'Server misconfiguration: BACKEND_URL is not set on Vercel' },
        { status: 500 }
      );
    }
    
    // Get request body
    const body = await request.json();

    // Forward the request to the backend API
    const response = await fetch(`${BACKEND_URL}/api/generate-portfolio-from-wizard`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.RAILWAY_API_KEY || ''
      },
      body: JSON.stringify(body)
    });

    // Get response data and pass through backend status
    const text = await response.text();
    let data: any;
    try {
      data = JSON.parse(text);
    } catch {
      data = { raw: text };
    }
    return NextResponse.json(data, { status: response.status });
    
  } catch (error: any) {
    console.error('API Proxy Error:', error);
    return NextResponse.json(
      { error: error.message || 'An error occurred while processing your request' },
      { status: 500 }
    );
  }
}
