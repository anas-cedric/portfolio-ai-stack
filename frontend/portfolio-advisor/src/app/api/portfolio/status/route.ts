import { NextRequest, NextResponse } from "next/server";
import { getKindeServerSession } from "@kinde-oss/kinde-auth-nextjs/server";
import { alpaca } from "@/lib/alpacaBroker";

// Test endpoint to verify Alpaca connection
export async function GET(req: NextRequest) {
  try {
    // Check authentication
    const { isAuthenticated } = getKindeServerSession();
    
    if (!(await isAuthenticated())) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // Test Alpaca connection by getting firm account
    const firmAccountId = process.env.ALPACA_FIRM_ACCOUNT_ID;
    
    if (!firmAccountId) {
      return NextResponse.json({ 
        error: "Alpaca not configured",
        message: "Missing ALPACA_FIRM_ACCOUNT_ID environment variable"
      }, { status: 500 });
    }

    // Try to get the firm account details
    const { data } = await alpaca.get(`/accounts/${firmAccountId}`);
    
    return NextResponse.json({
      status: "connected",
      firmAccount: {
        id: data.id,
        status: data.status,
        buying_power: data.buying_power,
        cash: data.cash
      },
      message: "Alpaca Broker API connected successfully"
    });
    
  } catch (error: any) {
    console.error('Alpaca status check failed:', error?.response?.data || error);
    
    return NextResponse.json({ 
      status: "error",
      error: error?.response?.data?.message || error.message,
      details: error?.response?.data
    }, { status: 500 });
  }
}