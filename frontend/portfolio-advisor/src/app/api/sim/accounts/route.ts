import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const BACKEND_URL = process.env.NODE_ENV === 'development'
      ? 'http://localhost:8000'
      : process.env.BACKEND_URL || ''

    if (process.env.NODE_ENV !== 'development' && !BACKEND_URL) {
      return NextResponse.json(
        { error: 'Server misconfiguration: BACKEND_URL is not set on Vercel' },
        { status: 500 }
      )
    }

    const body = await request.json()

    const resp = await fetch(`${BACKEND_URL}/api/v1/sim/accounts`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': request.headers.get('x-api-key') || ''
      },
      body: JSON.stringify(body)
    })

    const text = await resp.text()
    let data: any
    try { data = JSON.parse(text) } catch { data = { raw: text } }
    return NextResponse.json(data, { status: resp.status })
  } catch (err: any) {
    console.error('Proxy error /api/sim/accounts', err)
    return NextResponse.json({ error: err.message || 'Proxy error' }, { status: 500 })
  }
}
