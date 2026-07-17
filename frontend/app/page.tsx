"use client";

import { useEffect, useRef, useState } from "react";

type Machine = {
  id: number;
  vibration: number;
  temperature: number;
  current: number;
  risk: number;
  status: "NORMAL" | "WARNING" | "CRITICAL";
};

const STATUS_COLORS: Record<string, string> = {
  NORMAL: "#10b981",
  WARNING: "#f59e0b",
  CRITICAL: "#ef4444",
};

export default function Home() {
  const [machines, setMachines] = useState<Machine[]>([]);
  const [history, setHistory] = useState<Record<number, number[]>>({});
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket("wss://predictive-maintenance-mining.onrender.com/ws/telemetry");
    ws.onmessage = (ev) => {
      const data: Machine[] = JSON.parse(ev.data);
      setMachines(data);
      setHistory((h) => {
        const next = { ...h };
        data.forEach((m) => {
          const arr = next[m.id] ?? [];
          next[m.id] = [...arr.slice(-59), m.risk];
        });
        return next;
      });
    };
    wsRef.current = ws;
    return () => ws.close();
  }, []);

  return (
    <main style={{ padding: 24, fontFamily: "sans-serif", background: "#0b1220", minHeight: "100vh", color: "#e2e8f0" }}>
      <h1 style={{ marginBottom: 4 }}>Predictive Maintenance Dashboard</h1>
      <p style={{ color: "#94a3b8", marginBottom: 24 }}>
        Live sensor telemetry (vibration, temperature, current draw) with ML-based failure-risk prediction
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 16 }}>
        {machines.map((m) => (
          <div
            key={m.id}
            style={{
              background: "#111827",
              border: `2px solid ${STATUS_COLORS[m.status]}`,
              borderRadius: 10,
              padding: 16,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h3 style={{ margin: 0 }}>Machine {m.id}</h3>
              <span
                style={{
                  background: STATUS_COLORS[m.status],
                  color: "#0b1220",
                  fontWeight: 700,
                  fontSize: 12,
                  padding: "2px 8px",
                  borderRadius: 6,
                }}
              >
                {m.status}
              </span>
            </div>

            <div style={{ marginTop: 12, fontSize: 13, lineHeight: 1.7 }}>
              <div>Vibration: <b>{m.vibration}</b> mm/s</div>
              <div>Temperature: <b>{m.temperature}</b> C</div>
              <div>Current draw: <b>{m.current}</b> A</div>
              <div>Failure risk: <b style={{ color: STATUS_COLORS[m.status] }}>{(m.risk * 100).toFixed(1)}%</b></div>
            </div>

            <svg width={"100%"} height={50} style={{ marginTop: 10, background: "#0b1220" }} viewBox="0 0 240 50">
              {(history[m.id] ?? []).map((v, i) => (
                <rect key={i} x={i * 4} y={50 - v * 50} width={3} height={v * 50} fill={STATUS_COLORS[m.status]} />
              ))}
            </svg>
          </div>
        ))}
      </div>

      <h3 style={{ marginTop: 32 }}>Legend</h3>
      <ul style={{ fontSize: 13, lineHeight: 1.6, listStyle: "none", padding: 0 }}>
        <li><span style={{ color: STATUS_COLORS.NORMAL }}>■</span> Normal (risk under 40%)</li>
        <li><span style={{ color: STATUS_COLORS.WARNING }}>■</span> Warning (risk 40-70%)</li>
        <li><span style={{ color: STATUS_COLORS.CRITICAL }}>■</span> Critical (risk over 70%) - schedule maintenance</li>
      </ul>
    </main>
  );
}
