"use client";

import { useEffect, useRef, useState } from "react";
import { DeskUpdate } from "@/lib/types";

const GATEWAY = process.env.NEXT_PUBLIC_GATEWAY_URL || "http://localhost:8080";
const WS_URL = GATEWAY.replace(/^http/, "ws") + "/ws/desk";

export default function Page() {
  const [u, setU] = useState<DeskUpdate | null>(null);
  const [connected, setConnected] = useState(false);
  const [latencies, setLatencies] = useState<number[]>([]);
  const [equitySeries, setEquitySeries] = useState<number[]>([]);
  const bookRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (e) => {
      try {
        const up: DeskUpdate = JSON.parse(e.data);
        setU(up);
        setLatencies((p) => [...p.slice(-79), up.latency_ms]);
        setEquitySeries((p) => [...p.slice(-119), up.equity]);
      } catch {
        /* ignore */
      }
    };
    return () => ws.close();
  }, []);

  // draw order-book depth
  useEffect(() => {
    const c = bookRef.current;
    if (!c || !u) return;
    const ctx = c.getContext("2d");
    if (!ctx) return;
    c.width = c.clientWidth;
    c.height = c.clientHeight;
    ctx.clearRect(0, 0, c.width, c.height);
    const bids = u.book.bids || [];
    const asks = u.book.asks || [];
    const maxSize = Math.max(1, ...bids.map((b) => b[1]), ...asks.map((a) => a[1]));
    const rowH = 18;
    const midX = c.width / 2;
    bids.slice(0, 10).forEach((b, i) => {
      const w = (b[1] / maxSize) * (midX - 60);
      ctx.fillStyle = "rgba(38,208,124,0.25)";
      ctx.fillRect(midX - w, i * rowH, w, rowH - 2);
      ctx.fillStyle = "#26d07c";
      ctx.font = "12px ui-monospace";
      ctx.fillText(`${b[0].toFixed(2)}  ${b[1].toFixed(1)}`, 6, i * rowH + 13);
    });
    asks.slice(0, 10).forEach((a, i) => {
      const w = (a[1] / maxSize) * (midX - 60);
      ctx.fillStyle = "rgba(255,84,112,0.25)";
      ctx.fillRect(midX, i * rowH, w, rowH - 2);
      ctx.fillStyle = "#ff5470";
      ctx.font = "12px ui-monospace";
      ctx.fillText(`${a[0].toFixed(2)}  ${a[1].toFixed(1)}`, midX + 6, i * rowH + 13);
    });
  }, [u]);

  const spark = (data: number[], color: string) => {
    const max = Math.max(1e-9, ...data);
    const min = Math.min(...data, 0);
    const pts = data
      .map((v, i) => `${(i / Math.max(1, data.length - 1)) * 100},${100 - ((v - min) / (max - min || 1)) * 100}`)
      .join(" ");
    return (
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ width: "100%", height: 60 }}>
        <polyline points={pts} fill="none" stroke={color} strokeWidth={1.5} vectorEffect="non-scaling-stroke" />
      </svg>
    );
  };

  const f = u?.features;
  const a = u?.action;
  const avgLat = latencies.length ? latencies.reduce((x, y) => x + y, 0) / latencies.length : 0;

  return (
    <main style={{ maxWidth: 1080, margin: "0 auto", padding: 20 }}>
      <header style={{ display: "flex", gap: 12, alignItems: "baseline" }}>
        <strong style={{ fontSize: 18 }}>hfa</strong>
        <span style={{ color: "var(--muted)" }}>trading desk · Go ingest · Rust matcher · Python RL brain</span>
        <span style={{ marginLeft: "auto", color: connected ? "var(--bid)" : "var(--muted)" }}>
          {connected ? "● live" : "○ offline"}
        </span>
      </header>

      <section style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 12, marginTop: 14 }}>
        <div className="card">
          <div style={{ color: "var(--muted)", marginBottom: 6 }}>ORDER BOOK DEPTH</div>
          <canvas ref={bookRef} style={{ width: "100%", height: 200 }} />
        </div>
        <div className="card">
          <div style={{ color: "var(--muted)" }}>AGENT</div>
          <div
            className="big"
            style={{ color: a?.action === "BUY" ? "var(--bid)" : a?.action === "SELL" ? "var(--ask)" : "var(--muted)" }}
          >
            {a?.action ?? "—"}
          </div>
          <div style={{ color: "var(--muted)" }}>{a?.reason ?? ""}</div>
          <div style={{ marginTop: 10, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            <Stat label="mid" value={f ? f.mid.toFixed(2) : "—"} />
            <Stat label="spread" value={f ? f.spread.toFixed(3) : "—"} />
            <Stat label="OBI" value={f ? f.obi.toFixed(2) : "—"} />
            <Stat label="micro" value={f ? f.microprice.toFixed(3) : "—"} />
            <Stat label="position" value={u ? String(u.position) : "—"} />
            <Stat label="equity" value={u ? `$${u.equity.toLocaleString()}` : "—"} />
          </div>
        </div>
      </section>

      <section style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 12 }}>
        <div className="card">
          <div style={{ color: "var(--muted)" }}>EQUITY</div>
          {spark(equitySeries, "#26d07c")}
        </div>
        <div className="card">
          <div style={{ color: "var(--muted)" }}>ROUND-TRIP LATENCY · avg {avgLat.toFixed(2)} ms</div>
          {spark(latencies, "#4880ff")}
        </div>
      </section>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div style={{ color: "var(--muted)", fontSize: 11 }}>{label}</div>
      <div style={{ fontWeight: 700 }}>{value}</div>
    </div>
  );
}
