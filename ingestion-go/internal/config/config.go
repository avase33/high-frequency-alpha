// Package config loads concentrator settings from the environment.
package config

import (
	"os"
	"strconv"
)

type Config struct {
	Addr       string
	MatcherURL string
	BrainURL   string
	TickMs     int
}

func Load() Config {
	return Config{
		Addr:       env("HFA_ADDR", ":8080"),
		MatcherURL: env("HFA_MATCHER_URL", "http://localhost:8091"),
		BrainURL:   env("HFA_BRAIN_URL", "http://localhost:8000"),
		TickMs:     envInt("HFA_TICK_MS", 250),
	}
}

func env(k, def string) string {
	if v, ok := os.LookupEnv(k); ok && v != "" {
		return v
	}
	return def
}

func envInt(k string, def int) int {
	if v, ok := os.LookupEnv(k); ok {
		if n, err := strconv.Atoi(v); err == nil {
			return n
		}
	}
	return def
}
