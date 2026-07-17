export interface Features {
  mid: number;
  spread: number;
  obi: number;
  obi_ma: number;
  microprice: number;
  best_bid: number;
  best_ask: number;
}

export interface AgentAction {
  action: string;
  price: number;
  size: number;
  value: number;
  reason: string;
  risk_ok: boolean;
}

export interface DeskUpdate {
  ts: number;
  book: { bids: [number, number][]; asks: [number, number][] };
  features: Features;
  action: AgentAction;
  position: number;
  equity: number;
  latency_ms: number;
}
