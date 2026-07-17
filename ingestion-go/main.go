// Command hfa-ingestion is the market-data concentrator: it drives the synthetic
// (or live) feed through the Rust matcher and Python brain and streams the desk
// state to trading terminals over WebSocket.
package main

import (
	"encoding/json"
	"log"
	"net/http"

	"github.com/gorilla/websocket"

	"github.com/avase33/high-frequency-alpha/ingestion/internal/config"
	"github.com/avase33/high-frequency-alpha/ingestion/internal/feed"
	"github.com/avase33/high-frequency-alpha/ingestion/internal/hub"
)

type App struct {
	cfg config.Config
	hub *hub.Hub
}

var upgrader = websocket.Upgrader{CheckOrigin: func(r *http.Request) bool { return true }}

func (a *App) handleWS(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		return
	}
	client := a.hub.Add()
	defer func() {
		a.hub.Remove(client)
		conn.Close()
	}()
	go func() {
		for {
			if _, _, err := conn.ReadMessage(); err != nil {
				a.hub.Remove(client)
				return
			}
		}
	}()
	for msg := range client.Send {
		if err := conn.WriteMessage(websocket.TextMessage, msg); err != nil {
			return
		}
	}
}

func (a *App) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]any{
		"status": "ok", "service": "ingestion", "clients": a.hub.Count(),
		"matcher": a.cfg.MatcherURL, "brain": a.cfg.BrainURL,
	})
}

func main() {
	cfg := config.Load()
	h := hub.New()
	app := &App{cfg: cfg, hub: h}

	// Drive the market pipeline in the background.
	go feed.NewEngine(cfg, h).Run()

	mux := http.NewServeMux()
	mux.HandleFunc("GET /health", app.handleHealth)
	mux.HandleFunc("GET /ws/desk", app.handleWS)

	log.Printf("hfa ingestion (http %s) → matcher=%s brain=%s tick=%dms",
		cfg.Addr, cfg.MatcherURL, cfg.BrainURL, cfg.TickMs)
	if err := http.ListenAndServe(cfg.Addr, mux); err != nil {
		log.Fatal(err)
	}
}
