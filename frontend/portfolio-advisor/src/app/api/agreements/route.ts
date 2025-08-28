import { NextResponse } from 'next/server'
import { AGREEMENTS } from '@/config/agreements'

export async function GET() {
  return NextResponse.json({ agreements: AGREEMENTS })
}
