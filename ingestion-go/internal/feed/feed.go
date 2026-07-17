// Package feed drives the pipeline: it generates a synthetic market event stream
// (or would read exchange WebSockets), submits batches to the Rust matcher, asks
// the Python brain for an action, applies the fill, and broadcasts the desk state.
package feed

import (
	"bytes"
	"encoding/json"
	"math"
	"math/rand"
	"net/http"
	"time"

	"github.com/avase33/high-frequency-alpha/ingestion/internal/config"
	"github.com/avase33/high-frequency-alpha/ingestion/internal/hub"
)

type Event struct {
	ID    uint64  `json:"id"`
	Side  string  `json:"side"`
	Price float64 `json:"price"`
	Size  float64 `json:"size"`
	Kind  string  `json:"kind"`
}

type book struct {
	Bids [][2]float64 `json:"bids"`
	Asks [][2]float64 `json:"asks"`
}

type submitResp struct {
	Book     book               `json:"book"`
	Features map[string]float64 `json:"features"`
}

type action struct {
	Action string  `json:"action"`
	Price  float64 `json:"price"`
	Size   float64 `json:"size"`
	Value  float64 `json:"value"`
	Reason string  `json:"reason"`
	RiskOk bool    `json:"risk_ok"`
}

type Engine struct {
	cfg      config.Config
	hub      *hub.Hub
	http     *http.Client
	rng      *rand.Rand
	mid      float64
	seq      uint64
	position float64
	cash     float64
	equity   float64
	peak     float64
}

func NewEngine(cfg config.Config, h *hub.Hub) *Engine {
	return &Engine{
		cfg: cfg, hub: h, http: &http.Client{Timeout: 2 * time.Second},
		rng: rand.New(rand.NewSource(1)),
		mid: 100.0, cash: 100_000, equity: 100_000, peak: 100_000,
	}
}

func round2(x float64) float64 { return math.Round(x*100) / 100 }

// GenBatch produces a small burst of resting limit orders around the mid, plus an
// occasional marketable order, then drifts the mid.
func (e *Engine) GenBatch() []Event {
	evs := make([]Event, 0, 7)
	for i := 0; i < 3; i++ {
		e.seq++
		evs = append(evs, Event{e.seq, "bid", round2(e.mid - 0.01*float64(i+1)), 1 + e.rng.Float64()*4, "limit"})
		e.seq++
		evs = append(evs, Event{e.seq, "ask", round2(e.mid + 0.01*float64(i+1)), 1 + e.rng.Float64()*4, "limit"})
	}
	if e.rng.Float64() < 0.3 {
		e.seq++
		side := "bid"
		if e.rng.Float64() < 0.5 {
			side = "ask"
		}
		evs = append(evs, Event{e.seq, side, round2(e.mid), 1 + e.rng.Float64()*2, "market"})
	}
	e.mid = math.Max(1.0, e.mid+e.rng.NormFloat64()*0.02)
	return evs
}

func (e *Engine) Run() {
	ticker := time.NewTicker(time.Duration(e.cfg.TickMs) * time.Millisecond)
	defer ticker.Stop()
	for range ticker.C {
		e.step()
	}
}

func (e *Engine) step() {
	t0 := time.Now()
	batch := e.GenBatch()

	var sr submitResp
	if err := e.post(e.cfg.MatcherURL+"/submit", map[string]any{"events": batch}, &sr); err != nil {
		return
	}
	var act action
	_ = e.post(e.cfg.BrainURL+"/decide", map[string]any{
		"features": sr.Features, "position": e.position, "cash": e.cash,
		"equity": e.equity, "peak_equity": e.peak,
	}, &act)

	if act.RiskOk && act.Size > 0 {
		switch act.Action {
		case "BUY":
			e.position += act.Size
			e.cash -= act.Size * act.Price
		case "SELL":
			e.position -= act.Size
			e.cash += act.Size * act.Price
		}
	}
	if mid := sr.Features["mid"]; mid > 0 {
		e.equity = e.cash + e.position*mid
		if e.equity > e.peak {
			e.peak = e.equity
		}
	}

	e.hub.Broadcast(map[string]any{
		"ts":         float64(time.Now().Unix()),
		"book":       sr.Book,
		"features":   sr.Features,
		"action":     act,
		"position":   round2(e.position),
		"equity":     round2(e.equity),
		"latency_ms": float64(time.Since(t0).Microseconds()) / 1000.0,
	})
}

func (e *Engine) post(url string, payload any, out any) error {
	body, err := json.Marshal(payload)
	if err != nil {
		return err
	}
	resp, err := e.http.Post(url, "application/json", bytes.NewReader(body))
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	return json.NewDecoder(resp.Body).Decode(out)
}
