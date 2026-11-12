//! WebSocket routes the Rust server serves itself instead of relaying them to Django Channels.
//!
//! Enabled per route with `web.rust_websocket_routes`. Routes that aren't enabled keep going
//! through the relay in [`super::core`], so this falls back to the existing behavior.
//!
//! Python stays authoritative: it authorizes each handshake (see [`contract`]) and keeps sending
//! messages through the PostgreSQL channel layer, which the Rust server reads (see [`layer`]).

use std::sync::Arc;

use ak_axum::router::wrap_router;
use ak_common::{
    Arbiter, Tasks,
    config::{self, schema::RustWebsocketRoute},
    db,
};
use axum::{Router, routing::any};
use eyre::Result;
use tracing::info;

use crate::server::ServerClient;

mod client;
mod codec;
mod contract;
mod layer;

const METRIC_CONNECTIONS: &str = "authentik_main_websocket_connections";

struct WebsocketState {
    contract: contract::Contract,
    layer: Arc<layer::Layer>,
    arbiter: Arbiter,
}

/// Starts receiving channel layer messages and returns the router for the enabled routes.
///
/// Returns an empty router when no route is enabled, so every WebSocket keeps going through
/// the relay.
pub(super) fn start(tasks: &mut Tasks, client: ServerClient) -> Result<Router> {
    let routes = &config::get().web.rust_websocket_routes;
    if routes.is_empty() {
        return Ok(Router::new());
    }
    info!(?routes, "serving WebSocket routes in the server");

    metrics::describe_gauge!(
        METRIC_CONNECTIONS,
        "WebSocket connections the server serves itself"
    );
    metrics::describe_counter!(
        layer::METRIC_DROPPED,
        "Channel layer messages dropped because a WebSocket connection wasn't keeping up"
    );

    let arbiter = tasks.arbiter();
    let layer = Arc::new(layer::Layer::new(db::get().clone()));
    tasks
        .build_task()
        .name(&format!("{}::layer::run", module_path!()))
        .spawn(Arc::clone(&layer).run(arbiter.clone()))?;

    Ok(router(
        Arc::new(WebsocketState {
            contract: contract::Contract::new(client),
            layer,
            arbiter,
        }),
        routes,
    ))
}

fn router(state: Arc<WebsocketState>, routes: &[RustWebsocketRoute]) -> Router {
    let mut app = Router::new();
    for route in routes {
        app = match route {
            RustWebsocketRoute::Client => app.route("/ws/client/", any(client::handler)),
        };
    }
    wrap_router(app.with_state(state), config::get().debug)
}

#[cfg(test)]
mod tests;
