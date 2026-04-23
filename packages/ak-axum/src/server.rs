//! Utilities to run an axum server.

use std::{net, os::unix};

use ak_common::arbiter::{Arbiter, Tasks};
use axum::Router;
use axum_server::{
    Handle,
    accept::DefaultAcceptor,
    tls_rustls::{RustlsAcceptor, RustlsConfig},
};
use eyre::Result;
use tracing::{info, trace};

use crate::accept::{proxy_protocol::ProxyProtocolAcceptor, tls::TlsAcceptor};

async fn run_plain(
    arbiter: Arbiter,
    name: &str,
    router: Router,
    addr: net::SocketAddr,
    allow_failure: bool,
) -> Result<()> {
    info!(addr = addr.to_string(), "starting {name} server");

    let handle = Handle::new();
    arbiter.add_net_handle(handle.clone()).await;

    let res = axum_server::Server::bind(addr)
        .acceptor(ProxyProtocolAcceptor::new().acceptor(DefaultAcceptor::new()))
        .handle(handle)
        .serve(router.into_make_service_with_connect_info::<net::SocketAddr>())
        .await;
    if res.is_err() && allow_failure {
        arbiter.shutdown().await;
        return Ok(());
    }
    res?;

    Ok(())
}

/// Start a plaintext server.
///
/// `name` is only used for observability purposes and should describe which module is starting the
/// server.
///
/// `allow_failure` allows the server to fail silently.
pub fn start_plain(
    tasks: &mut Tasks,
    name: &'static str,
    router: Router,
    addr: net::SocketAddr,
    allow_failure: bool,
) -> Result<()> {
    let arbiter = tasks.arbiter();
    tasks
        .build_task()
        .name(&format!("{}::run_plain({name}, {addr})", module_path!()))
        .spawn(run_plain(arbiter, name, router, addr, allow_failure))?;
    Ok(())
}

pub(crate) async fn run_unix(
    arbiter: Arbiter,
    name: &str,
    router: Router,
    addr: unix::net::SocketAddr,
    allow_failure: bool,
) -> Result<()> {
    info!(?addr, "starting {name} server");

    let handle = Handle::new();
    arbiter.add_unix_handle(handle.clone()).await;

    if !allow_failure && let Some(path) = addr.as_pathname() {
        trace!(?addr, "removing socket");
        if let Err(err) = std::fs::remove_file(path) {
            trace!(?err, "failed to remove socket, ignoring");
        }
    }
    let res = axum_server::Server::bind(addr.clone())
        .acceptor(DefaultAcceptor::new())
        .handle(handle)
        .serve(router.into_make_service())
        .await;
    if !allow_failure && let Some(path) = addr.as_pathname() {
        trace!(?addr, "removing socket");
        if let Err(err) = std::fs::remove_file(path) {
            trace!(?err, "failed to remove socket, ignoring");
        }
    }
    if res.is_err() && allow_failure {
        arbiter.shutdown().await;
        return Ok(());
    }
    res?;

    Ok(())
}

/// Start a Unix socket server.
///
/// `name` is only used for observability purposes and should describe which module is starting the
/// server.
///
/// `allow_failure` allows the server to fail silently.
pub fn start_unix(
    tasks: &mut Tasks,
    name: &'static str,
    router: Router,
    addr: unix::net::SocketAddr,
    allow_failure: bool,
) -> Result<()> {
    let arbiter = tasks.arbiter();
    tasks
        .build_task()
        .name(&format!("{}::run_unix({name}, {addr:?})", module_path!()))
        .spawn(run_unix(arbiter, name, router, addr, allow_failure))?;
    Ok(())
}

async fn run_tls(
    arbiter: Arbiter,
    name: &str,
    router: Router,
    addr: net::SocketAddr,
    config: RustlsConfig,
) -> Result<()> {
    info!(addr = addr.to_string(), "starting {name} server");

    let handle = Handle::new();
    arbiter.add_net_handle(handle.clone()).await;

    axum_server::Server::bind(addr)
        .acceptor(ProxyProtocolAcceptor::new().acceptor(TlsAcceptor::new(
            RustlsAcceptor::new(config).acceptor(DefaultAcceptor::new()),
        )))
        .handle(handle)
        .serve(router.into_make_service_with_connect_info::<net::SocketAddr>())
        .await?;

    Ok(())
}

/// Start a TLS server.
///
/// `name` is only used for observability purposes and should describe which module is starting the
/// server.
pub fn start_tls(
    tasks: &mut Tasks,
    name: &'static str,
    router: Router,
    addr: net::SocketAddr,
    config: RustlsConfig,
) -> Result<()> {
    let arbiter = tasks.arbiter();
    tasks
        .build_task()
        .name(&format!("{}::run_tls({name}, {addr})", module_path!()))
        .spawn(run_tls(arbiter, name, router, addr, config))?;
    Ok(())
}
