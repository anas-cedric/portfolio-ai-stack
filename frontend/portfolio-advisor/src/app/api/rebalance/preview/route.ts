import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const BACKEND_URL = process.env.NODE_ENV === 'development'
      ? 'http://localhost:8000'
      : process.env.BACKEND_URL || '';

    const body = await request.json();

    const resp = await fetch(`${BACKEND_URL}/api/rebalance/preview`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': request.headers.get('x-api-key') || '',
      },
      body: JSON.stringify(body),
    });

    const data = await resp.json();
    return NextResponse.json(data, { status: resp.status });
  } catch (error: any) {
    console.error('Rebalance Preview API Error:', error);
    return NextResponse.json(
      { error: error?.message || 'Failed to preview rebalance' },
      { status: 500 }
    );
  }
}
