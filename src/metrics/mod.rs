use std::net::SocketAddr;

use axum::{Router, routing::any};
use axum_server::Handle;
use eyre::Result;
use tracing::info;

mod handlers;

pub(super) fn build_router() -> Router {
    Router::new().fallback(any(handlers::metrics_handler))
}

pub(super) async fn start_server(
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
