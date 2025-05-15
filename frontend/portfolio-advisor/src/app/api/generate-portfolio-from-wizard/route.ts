import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    // For local development
    const BACKEND_URL = process.env.NODE_ENV === 'development' 
      ? 'http://localhost:8000' 
      : process.env.BACKEND_URL || '';
    
    // Get request body
    const body = await request.json();

    // Forward the request to the backend API
    const response = await fetch(`${BACKEND_URL}/api/generate-portfolio-from-wizard`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': request.headers.get('x-api-key') || ''
      },
      body: JSON.stringify(body)
    });

    // Get response data
    const data = await response.json();

    // Return response
    return NextResponse.json(data);
    
  } catch (error: any) {
    console.error('API Proxy Error:', error);
    return NextResponse.json(
      { error: error.message || 'An error occurred while processing your request' },
      { status: 500 }
    );
  }
}
