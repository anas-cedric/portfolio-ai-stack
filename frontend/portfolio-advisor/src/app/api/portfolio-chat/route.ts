import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const BACKEND_URL = process.env.NODE_ENV === 'development' 
      ? 'http://localhost:8000' 
      : process.env.BACKEND_URL || '';
    
    const body = await request.json();

    const response = await fetch(`${BACKEND_URL}/api/portfolio-chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': request.headers.get('x-api-key') || ''
      },
      body: JSON.stringify(body)
    });

    const data = await response.json();
    return NextResponse.json(data);
    
  } catch (error: any) {
    console.error('Portfolio Chat API Error:', error);
    return NextResponse.json(
      { error: error.message || 'An error occurred during chat' },
      { status: 500 }
    );
  }
}