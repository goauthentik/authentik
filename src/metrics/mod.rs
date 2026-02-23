use std::{
    net::SocketAddr,
    sync::{Arc, OnceLock},
};

use axum::{Router, routing::any};
use axum_server::Handle;
use eyre::Result;
use prometheus_client::registry::{Metric, Registry};
use tokio::sync::RwLock;
use tracing::info;

mod handlers;

static REGISTRY: OnceLock<Arc<RwLock<Registry>>> = OnceLock::new();

pub(super) fn init() {
    REGISTRY.get_or_init(|| Arc::new(RwLock::new(Registry::default())));
}

pub(super) async fn register<N: Into<String>, H: Into<String>>(
    name: N,
    help: H,
    metric: impl Metric,
) {
    REGISTRY
        .get()
        .expect("failed to get registry, has it been initialized?")
        .write()
        .await
        .register(name, help, metric);
}

pub(super) fn build_router() -> Router {
    Router::new().fallback(any(handlers::metrics_handler))
}

pub(super) async fn run_server(
    router: Router,
    addr: SocketAddr,
    handle: Handle<SocketAddr>,
) -> Result<()> {
    info!(addr = addr.to_string(), "starting metrics server");
    axum_server::Server::bind(addr)
        .handle(handle)
        .serve(router.into_make_service_with_connect_info::<SocketAddr>())
        .await?;

    Ok(())
}
