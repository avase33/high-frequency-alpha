//! In-memory aggregated limit order book + microstructure features.
//!
//! Prices are quantised to integer ticks so we can key `BTreeMap`s (f64 isn't
//! `Ord`); each level stores aggregate resting size. Incoming orders match against
//! the opposite side price-time, and we compute Order Book Imbalance (OBI),
//! micro-price and spread — the features the RL brain trades on. Zero heap churn
//! beyond the maps.

use std::collections::{BTreeMap, VecDeque};

use serde::{Deserialize, Serialize};

const TICK: f64 = 100.0;
const OBI_DEPTH: usize = 5;
const OBI_WINDOW: usize = 20;

fn to_ticks(p: f64) -> i64 {
    (p * TICK).round() as i64
}
fn from_ticks(t: i64) -> f64 {
    t as f64 / TICK
}

#[derive(Clone, Deserialize)]
pub struct Event {
    #[serde(default)]
    pub id: u64,
    pub side: String, // "bid" | "ask"
    pub price: f64,
    pub size: f64,
    #[serde(default = "default_kind")]
    pub kind: String, // "limit" | "market" | "cancel"
}

fn default_kind() -> String {
    "limit".to_string()
}

#[derive(Serialize, Clone)]
pub struct Trade {
    pub price: f64,
    pub size: f64,
}

#[derive(Serialize, Clone, Default)]
pub struct Features {
    pub mid: f64,
    pub spread: f64,
    pub obi: f64,
    pub obi_ma: f64,
    pub microprice: f64,
    pub best_bid: f64,
    pub best_ask: f64,
}

#[derive(Default)]
pub struct OrderBook {
    bids: BTreeMap<i64, f64>, // best = highest key
    asks: BTreeMap<i64, f64>, // best = lowest key
    obi_window: VecDeque<f64>,
}

impl OrderBook {
    pub fn new() -> Self {
        Self::default()
    }

    fn best_bid(&self) -> Option<i64> {
        self.bids.keys().next_back().copied()
    }
    fn best_ask(&self) -> Option<i64> {
        self.asks.keys().next().copied()
    }

    fn add(&mut self, side_bid: bool, ticks: i64, size: f64) {
        let book = if side_bid { &mut self.bids } else { &mut self.asks };
        *book.entry(ticks).or_insert(0.0) += size;
    }

    fn reduce(&mut self, side_bid: bool, ticks: i64, size: f64) {
        let book = if side_bid { &mut self.bids } else { &mut self.asks };
        if let Some(v) = book.get_mut(&ticks) {
            *v -= size;
            if *v <= 1e-9 {
                book.remove(&ticks);
            }
        }
    }

    /// Match an aggressive order against the opposite side; returns trades and any
    /// unfilled remainder (which a limit order will rest).
    fn cross(&mut self, incoming_bid: bool, limit_ticks: Option<i64>, mut size: f64) -> (Vec<Trade>, f64) {
        let mut trades = Vec::new();
        loop {
            if size <= 1e-9 {
                break;
            }
            let best = if incoming_bid { self.best_ask() } else { self.best_bid() };
            let Some(level) = best else { break };
            if let Some(lt) = limit_ticks {
                let crosses = if incoming_bid { level <= lt } else { level >= lt };
                if !crosses {
                    break;
                }
            }
            let avail = if incoming_bid { self.asks[&level] } else { self.bids[&level] };
            let traded = size.min(avail);
            trades.push(Trade { price: from_ticks(level), size: traded });
            self.reduce(!incoming_bid, level, traded);
            size -= traded;
        }
        (trades, size)
    }

    pub fn apply(&mut self, ev: &Event) -> Vec<Trade> {
        let is_bid = ev.side == "bid";
        let ticks = to_ticks(ev.price);
        match ev.kind.as_str() {
            "cancel" => {
                self.reduce(is_bid, ticks, ev.size);
                Vec::new()
            }
            "market" => {
                let (trades, _) = self.cross(is_bid, None, ev.size);
                trades
            }
            _ => {
                // limit: match crossable portion, rest the remainder
                let (trades, rest) = self.cross(is_bid, Some(ticks), ev.size);
                if rest > 1e-9 {
                    self.add(is_bid, ticks, rest);
                }
                trades
            }
        }
    }

    pub fn apply_all(&mut self, events: &[Event]) -> (Vec<Trade>, Features) {
        let mut all = Vec::new();
        for ev in events {
            all.extend(self.apply(ev));
        }
        (all, self.features())
    }

    fn top_size(&self, bids: bool, depth: usize) -> f64 {
        if bids {
            self.bids.values().rev().take(depth).sum()
        } else {
            self.asks.values().take(depth).sum()
        }
    }

    pub fn features(&mut self) -> Features {
        let mut f = Features::default();
        let b5 = self.top_size(true, OBI_DEPTH);
        let a5 = self.top_size(false, OBI_DEPTH);
        if b5 + a5 > 0.0 {
            f.obi = (b5 - a5) / (b5 + a5);
        }
        self.obi_window.push_back(f.obi);
        if self.obi_window.len() > OBI_WINDOW {
            self.obi_window.pop_front();
        }
        f.obi_ma = self.obi_window.iter().sum::<f64>() / self.obi_window.len().max(1) as f64;

        if let (Some(bbt), Some(bat)) = (self.best_bid(), self.best_ask()) {
            let (bb, ba) = (from_ticks(bbt), from_ticks(bat));
            f.best_bid = bb;
            f.best_ask = ba;
            f.mid = (bb + ba) / 2.0;
            f.spread = ba - bb;
            let bs = self.bids[&bbt];
            let asz = self.asks[&bat];
            if bs + asz > 0.0 {
                f.microprice = (bb * asz + ba * bs) / (bs + asz);
            }
        }
        f
    }

    pub fn levels(&self, depth: usize) -> (Vec<[f64; 2]>, Vec<[f64; 2]>) {
        let bids = self
            .bids
            .iter()
            .rev()
            .take(depth)
            .map(|(&t, &s)| [from_ticks(t), s])
            .collect();
        let asks = self
            .asks
            .iter()
            .take(depth)
            .map(|(&t, &s)| [from_ticks(t), s])
            .collect();
        (bids, asks)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn ev(side: &str, price: f64, size: f64, kind: &str) -> Event {
        Event { id: 0, side: side.into(), price, size, kind: kind.into() }
    }

    #[test]
    fn resting_limits_build_the_book() {
        let mut b = OrderBook::new();
        b.apply(&ev("bid", 100.0, 3.0, "limit"));
        b.apply(&ev("ask", 100.1, 2.0, "limit"));
        let f = b.features();
        assert!((f.best_bid - 100.0).abs() < 1e-9);
        assert!((f.best_ask - 100.1).abs() < 1e-9);
        assert!((f.mid - 100.05).abs() < 1e-9);
        assert!(f.spread > 0.0);
    }

    #[test]
    fn crossing_limit_generates_a_trade() {
        let mut b = OrderBook::new();
        b.apply(&ev("ask", 100.1, 2.0, "limit"));
        let trades = b.apply(&ev("bid", 100.2, 1.0, "limit")); // crosses the ask
        assert_eq!(trades.len(), 1);
        assert!((trades[0].price - 100.1).abs() < 1e-9);
        assert!((trades[0].size - 1.0).abs() < 1e-9);
    }

    #[test]
    fn obi_reflects_imbalance() {
        let mut b = OrderBook::new();
        b.apply(&ev("bid", 100.0, 9.0, "limit"));
        b.apply(&ev("ask", 100.1, 1.0, "limit"));
        let f = b.features();
        assert!(f.obi > 0.5); // heavy bid side
    }

    #[test]
    fn cancel_removes_size() {
        let mut b = OrderBook::new();
        b.apply(&ev("bid", 100.0, 5.0, "limit"));
        b.apply(&ev("bid", 100.0, 5.0, "cancel"));
        let (bids, _) = b.levels(5);
        assert!(bids.is_empty());
    }
}
