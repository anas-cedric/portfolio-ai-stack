import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const BACKEND_URL = process.env.BACKEND_URL || (process.env.NODE_ENV === 'development' ? 'http://localhost:8000' : '')
    const API_KEY = process.env.BACKEND_API_KEY || process.env.API_KEY || (process.env.NODE_ENV === 'development' ? 'demo_key' : '')

    if (process.env.NODE_ENV !== 'development' && (!BACKEND_URL || !API_KEY)) {
      return NextResponse.json(
        { error: 'Server misconfiguration: BACKEND_URL or API key missing' },
        { status: 500 }
      )
    }

    const body = await request.json()
    const ip = request.headers.get('x-forwarded-for') || request.headers.get('x-real-ip') || 'unknown'
    const ua = request.headers.get('user-agent') || 'unknown'
    const payload = { ...body, ip: body.ip ?? ip, user_agent: body.user_agent ?? ua }

    const resp = await fetch(`${BACKEND_URL}/agreements/accept`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': API_KEY,
      },
      body: JSON.stringify(payload)
    })

    const text = await resp.text()
    let data: any
    try { data = JSON.parse(text) } catch { data = { raw: text } }
    return NextResponse.json(data, { status: resp.status })
  } catch (err: any) {
    console.error('Proxy error /api/agreements/accept', err)
    return NextResponse.json({ error: err.message || 'Proxy error' }, { status: 500 })
  }
}
