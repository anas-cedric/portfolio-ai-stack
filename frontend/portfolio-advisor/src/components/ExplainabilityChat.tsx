"use client";

import React, { useEffect, useMemo, useRef, useState, FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Lock } from "lucide-react";

export type ExplainabilityChatProps = {
  enabled: boolean;
  reasonDisabled?: string;
  accountId?: string | null;
  status?: string | null;
  hasExecutedTrades?: boolean;
  holdings?: {
    accountId: string;
    cash: number;
    portfolio_value: number;
    positions: Array<{ symbol: string; qty: number; market_value: number; percent: number }>;
    cash_percent: number;
    as_of: string;
  } | null;
  orders?: {
    accountId: string;
    open_count: number;
    open_orders: Array<{
      id: string;
      client_order_id?: string;
      symbol: string;
      notional?: string;
      qty?: string;
      side: string;
      type: string;
      status: string;
      created_at: string;
    }>;
    as_of: string;
  } | null;
  apiKey?: string;
  userName?: string;
  userEmail?: string;
};

type ChatMessage = { role: "user" | "assistant"; content: string };

function limitWords(text: string, maxWords = 50): string {
  const words = text.trim().split(/\s+/);
  if (words.length <= maxWords) return text.trim();
  const trimmed = words.slice(0, maxWords).join(" ");
  return trimmed + "… If you want more detail, ask me to expand.";
}

export default function ExplainabilityChat({
  enabled,
  reasonDisabled,
  accountId,
  status,
  hasExecutedTrades,
  holdings,
  orders,
  apiKey = process.env.NEXT_PUBLIC_API_KEY || "test_api_key_for_development",
  userName,
  userEmail,
}: ExplainabilityChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string>("");

  const contextSummary = useMemo(() => {
    const pos = (holdings?.positions || [])
      .sort((a, b) => b.percent - a.percent)
      .slice(0, 10)
      .map((p) => ({ s: p.symbol, pct: Number(p.percent.toFixed(2)), qty: Number(p.qty) }));
    const openOrders = (orders?.open_orders || []).map((o) => ({ s: o.symbol, side: o.side, notional: o.notional, qty: o.qty, status: o.status }));
    return {
      account_id: accountId,
      status,
      has_executed_trades: !!hasExecutedTrades,
      as_of: holdings?.as_of || orders?.as_of,
      portfolio_value: holdings?.portfolio_value,
      cash: holdings?.cash,
      holdings_top10: pos,
      cash_percent: holdings?.cash_percent,
      open_orders: openOrders,
      user_name: userName,
      user_email: userEmail,
    };
  }, [accountId, status, hasExecutedTrades, holdings, orders]);

  useEffect(() => {
    if (messages.length === 0) {
      const intro = "Explain any position, pending orders, or cash level in under 50 words. Ask if the user wants more detail.";
      setMessages([{ role: "assistant", content: intro }]);
    }
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!enabled || isLoading || !input.trim()) return;

    const newUserMsg: ChatMessage = { role: "user", content: input.trim() };
    setMessages((prev) => [...prev, newUserMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const systemInstructions = [
        "You are an explainability assistant for a live brokerage portfolio.",
        "Use the provided account_context (holdings, cash, portfolio_value, open_orders, status).",
        "Reflect pending trades and executed positions if present.",
        "Strictly limit each response to 50 words or fewer. No long paragraphs. Short, clear sentences.",
        "If the user wants more, ask if they would like to expand or dive deeper.",
        "Do not provide individualized investment advice. Educational information only.",
        "You are not an RIA. Include a brief disclaimer if advice is implied.",
      ].join(" \n");

      const resp = await fetch("/api/portfolio-chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": apiKey,
        },
        body: JSON.stringify({
          conversation_id: conversationId,
          user_message: newUserMsg.content,
          conversation_history: messages.map((m) => ({ role: m.role, content: m.content })),
          metadata: {
            system_instructions: systemInstructions,
            account_context: contextSummary,
            conversation_state: 'complete',
          },
        }),
      });

      const data = await resp.json();
      if (data.conversation_id && data.conversation_id !== conversationId) {
        setConversationId(data.conversation_id);
      }

      let assistantText = typeof data.response === "string" ? data.response : JSON.stringify(data.response);
      assistantText = limitWords(assistantText, 50);

      setMessages((prev) => [...prev, { role: "assistant", content: assistantText }]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I ran into an error. Please try again." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Explainability Chat</CardTitle>
      </CardHeader>
      <CardContent>
        {!enabled ? (
          <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 border text-sm text-[#00121F]/70">
            <Lock className="w-4 h-4 mt-0.5" />
            <div>
              <div className="font-medium">Awaiting account funding</div>
              <div className="text-[#00121F]/60">
                {reasonDisabled || "This chat activates after your portfolio is funded and trades are pending or executed."}
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="max-h-[260px] overflow-y-auto pr-2 light-scrollbar">
              {messages.map((m, idx) => (
                <div key={idx} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"} mb-2`}>
                  <div className={`max-w-[80%] rounded-2xl px-3 py-2 ${m.role === "user" ? "bg-[#00121F]/5 text-[#00121F]" : "text-[#00121F]"} fade-in`}>
                    {m.content}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex items-center gap-2 text-sm text-[#00121F]/60">
                  <Loader2 className="w-4 h-4 animate-spin" /> Thinking…
                </div>
              )}
            </div>

            <form onSubmit={handleSubmit} className="flex items-center bg-white/80 backdrop-blur-sm border border-white/60 rounded-full">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={!enabled || isLoading}
                placeholder="Ask about a holding, cash, or orders"
                className="flex-1 bg-transparent outline-none text-sm text-[#00121F] placeholder:text-[#00121F]/40 px-4 py-2"
              />
              <Button type="submit" disabled={!enabled || isLoading || !input.trim()} className="mr-2 h-8 px-3 rounded-full">
                Send
              </Button>
            </form>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
