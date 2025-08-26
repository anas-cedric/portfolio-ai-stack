import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest, { params }: { params: { account_id: string } }) {
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
    const asOf = url.searchParams.get('as_of')
    const qs = asOf ? `?as_of=${encodeURIComponent(asOf)}` : ''

    const resp = await fetch(`${BACKEND_URL}/api/v1/sim/accounts/${params.account_id}${qs}`, {
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
    console.error('Proxy error /api/sim/accounts/[id]', err)
    return NextResponse.json({ error: err.message || 'Proxy error' }, { status: 500 })
  }
}
