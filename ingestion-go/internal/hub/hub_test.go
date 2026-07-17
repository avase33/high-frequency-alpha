package hub

import (
	"strings"
	"testing"
)

func TestHubBroadcastAndRemove(t *testing.T) {
	h := New()
	c := h.Add()
	if h.Count() != 1 {
		t.Fatalf("want 1 client, got %d", h.Count())
	}
	h.Broadcast(map[string]string{"action": "BUY"})
	msg := <-c.Send
	if !strings.Contains(string(msg), `"action":"BUY"`) {
		t.Fatalf("unexpected broadcast: %s", msg)
	}
	h.Remove(c)
	if h.Count() != 0 {
		t.Fatalf("want 0 clients, got %d", h.Count())
	}
}
