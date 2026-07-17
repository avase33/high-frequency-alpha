//! hfa matcher HTTP service (axum). Maintains one shared order book and exposes
//! /submit, /features, /book, /health. See proto/protocol.md.

use std::sync::Arc;

use axum::{
    extract::State,
    routing::{get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use tokio::sync::Mutex;

use hfa_matcher::book::{Event, Features, OrderBook, Trade};

type Shared = Arc<Mutex<OrderBook>>;

#[derive(Deserialize)]
struct SubmitReq {
    events: Vec<Event>,
}

#[derive(Serialize)]
struct BookLevels {
    bids: Vec<[f64; 2]>,
    asks: Vec<[f64; 2]>,
}

#[derive(Serialize)]
struct SubmitResp {
    book: BookLevels,
    trades: Vec<Trade>,
    features: Features,
}

async fn submit(State(s): State<Shared>, Json(req): Json<SubmitReq>) -> Json<SubmitResp> {
    let mut b = s.lock().await;
    let (trades, features) = b.apply_all(&req.events);
    let (bids, asks) = b.levels(10);
    Json(SubmitResp { book: BookLevels { bids, asks }, trades, features })
}

async fn features(State(s): State<Shared>) -> Json<Features> {
    let mut b = s.lock().await;
    Json(b.features())
}

async fn book(State(s): State<Shared>) -> Json<BookLevels> {
    let b = s.lock().await;
    let (bids, asks) = b.levels(10);
    Json(BookLevels { bids, asks })
}

async fn health() -> Json<serde_json::Value> {
    Json(serde_json::json!({ "status": "ok", "service": "matcher" }))
}

#[tokio::main]
async fn main() {
    let state: Shared = Arc::new(Mutex::new(OrderBook::new()));
    let app = Router::new()
        .route("/submit", post(submit))
        .route("/features", get(features))
        .route("/book", get(book))
        .route("/health", get(health))
        .with_state(state);

    let addr = std::env::var("MATCHER_ADDR").unwrap_or_else(|_| "0.0.0.0:8091".to_string());
    let listener = tokio::net::TcpListener::bind(&addr).await.expect("bind");
    println!("hfa matcher listening on {addr}");
    axum::serve(listener, app).await.expect("serve");
}
