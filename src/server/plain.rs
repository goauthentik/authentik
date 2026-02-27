use std::net::SocketAddr;

use axum::Router;
use axum_server::{Handle, accept::DefaultAcceptor};
use eyre::Result;
use tracing::info;

use crate::axum::accept::proxy_protocol::ProxyProtocolAcceptor;

pub(super) async fn run_server_plain(
    router: Router,
    addr: SocketAddr,
    handle: Handle<SocketAddr>,
) -> Result<()> {
    info!(addr = addr.to_string(), "starting plain server");
    axum_server::Server::bind(addr)
        .acceptor(ProxyProtocolAcceptor::new().acceptor(DefaultAcceptor::new()))
        .handle(handle)
        .serve(router.into_make_service_with_connect_info::<SocketAddr>())
        .await?;

    Ok(())
}
