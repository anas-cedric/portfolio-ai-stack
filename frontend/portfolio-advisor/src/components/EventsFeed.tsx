"use client";

import React, { useEffect, useState } from 'react';

export type CedricEvent = {
  id: string;
  kinde_user_id: string;
  account_id?: string | null;
  ts: string;
  type: 'ALLOCATION_PLACED' | 'EXECUTED' | 'DEPOSIT' | 'DRIFT_CHECK_NO_ACTION' | 'DRIFT_REBALANCE' | 'MARKET_NOTE' | 'MACRO_NOTE' | string;
  summary: string;
  description?: string | null;
  meta_json?: any;
};

const badgeFor = (type: CedricEvent['type']) => {
  const base = 'inline-block px-2 py-0.5 text-[11px] rounded border';
  switch (type) {
    case 'EXECUTED':
      return base + ' bg-green-50 text-green-700 border-green-200';
    case 'DRIFT_REBALANCE':
      return base + ' bg-blue-50 text-blue-700 border-blue-200';
    case 'DRIFT_CHECK_NO_ACTION':
      return base + ' bg-slate-50 text-slate-700 border-slate-200';
    case 'DEPOSIT':
      return base + ' bg-amber-50 text-amber-700 border-amber-200';
    case 'MARKET_NOTE':
    case 'MACRO_NOTE':
      return base + ' bg-purple-50 text-purple-700 border-purple-200';
    case 'ALLOCATION_PLACED':
      return base + ' bg-cyan-50 text-cyan-700 border-cyan-200';
    default:
      return base + ' bg-gray-50 text-gray-700 border-gray-200';
  }
};

export default function EventsFeed() {
  const [events, setEvents] = useState<CedricEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch('/api/events', { credentials: 'include' });
      if (!res.ok) {
        throw new Error(`Failed to fetch events (${res.status})`);
      }
      const data = await res.json();
      setEvents(Array.isArray(data.events) ? data.events : []);
    } catch (e: any) {
      setError(e?.message || 'Failed to load events');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="text-sm font-medium text-[#00121F]">Portfolio Events</div>
        <button
          onClick={load}
          className="text-xs text-[#00121F]/60 hover:text-[#00121F]"
          disabled={loading}
        >
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>
      {error && (
        <div className="text-xs text-red-600">{error}</div>
      )}
      {events.length === 0 && !loading && !error && (
        <div className="text-xs text-[#00121F]/60">No events yet.</div>
      )}
      <div className="space-y-2">
        {events.map((ev) => (
          <div key={ev.id} className="border border-[#00121F]/10 rounded p-3">
            <div className="flex items-center justify-between">
              <span className={badgeFor(ev.type)}>{ev.type}</span>
              <span className="text-[11px] text-[#00121F]/50">{new Date(ev.ts).toLocaleString()}</span>
            </div>
            <div className="mt-2 text-sm text-[#00121F] font-medium">{ev.summary}</div>
            {ev.description && (
              <div className="mt-1 text-xs text-[#00121F]/70">{ev.description}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
