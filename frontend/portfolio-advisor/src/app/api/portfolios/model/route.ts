import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
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

    const url = new URL(request.url)
    const bucket = url.searchParams.get('bucket')
    const version = url.searchParams.get('version') || 'v1'
    const qs = `?bucket=${encodeURIComponent(bucket || '')}&version=${encodeURIComponent(version)}`

    const resp = await fetch(`${BACKEND_URL}/api/v1/portfolios/model${qs}`, {
      method: 'GET',
      headers: {
        'x-api-key': request.headers.get('x-api-key') || ''
      }
    })

    const text = await resp.text()
    let data: any
    try { data = JSON.parse(text) } catch { data = { raw: text } }
    return NextResponse.json(data, { status: resp.status })
  } catch (err: any) {
    console.error('Proxy error /api/portfolios/model', err)
    return NextResponse.json({ error: err.message || 'Proxy error' }, { status: 500 })
  }
}
