package feed

import (
	"testing"

	"github.com/avase33/high-frequency-alpha/ingestion/internal/config"
	"github.com/avase33/high-frequency-alpha/ingestion/internal/hub"
)

func TestGenBatchProducesValidEvents(t *testing.T) {
	e := NewEngine(config.Config{}, hub.New())
	batch := e.GenBatch()
	if len(batch) < 6 {
		t.Fatalf("want >= 6 events, got %d", len(batch))
	}
	sawBid, sawAsk := false, false
	for _, ev := range batch {
		if ev.Side != "bid" && ev.Side != "ask" {
			t.Fatalf("bad side %q", ev.Side)
		}
		if ev.Kind != "limit" && ev.Kind != "market" {
			t.Fatalf("bad kind %q", ev.Kind)
		}
		if ev.Size <= 0 {
			t.Fatal("size must be positive")
		}
		sawBid = sawBid || ev.Side == "bid"
		sawAsk = sawAsk || ev.Side == "ask"
	}
	if !sawBid || !sawAsk {
		t.Fatal("batch should quote both sides")
	}
}

func TestSeqMonotonic(t *testing.T) {
	e := NewEngine(config.Config{}, hub.New())
	e.GenBatch()
	first := e.seq
	e.GenBatch()
	if e.seq <= first {
		t.Fatalf("seq should advance: %d -> %d", first, e.seq)
	}
}
