//! Utilities to run an axum server.

use std::{net, os::unix, path::PathBuf};

use ak_common::arbiter::{Arbiter, Tasks};
use axum::Router;
use axum_server::{
    Handle,
    accept::DefaultAcceptor,
    tls_rustls::{RustlsAcceptor, RustlsConfig},
};
use eyre::Result;
use tracing::{info, trace};

use crate::accept::{
    catch_panic::CatchPanicAcceptor, proxy_protocol::ProxyProtocolAcceptor, tls::TlsAcceptor,
};

async fn run_plain(
    arbiter: Arbiter,
    name: &str,
    router: Router,
    addr: net::SocketAddr,
) -> Result<()> {
    info!(addr = addr.to_string(), "starting {name} server");

    let handle = Handle::new();
    arbiter.add_net_handle(handle.clone()).await;

    axum_server::Server::bind(addr)
        .acceptor(CatchPanicAcceptor::new(
            ProxyProtocolAcceptor::new().acceptor(DefaultAcceptor::new()),
            arbiter.clone(),
        ))
        .handle(handle)
        .serve(router.into_make_service_with_connect_info::<net::SocketAddr>())
        .await?;

    Ok(())
}

/// Start a plaintext server.
///
/// `name` is only used for observability purposes and should describe which module is starting the
/// server.
pub fn start_plain(
    tasks: &mut Tasks,
    name: &'static str,
    router: Router,
    addr: net::SocketAddr,
) -> Result<()> {
    let arbiter = tasks.arbiter();
    tasks
        .build_task()
        .name(&format!("{}::run_plain({name}, {addr})", module_path!()))
        .spawn(run_plain(arbiter, name, router, addr))?;
    Ok(())
}

struct UnixSocketGuard(PathBuf);

impl Drop for UnixSocketGuard {
    fn drop(&mut self) {
        trace!(path = ?self.0, "removing socket");
        if let Err(err) = std::fs::remove_file(&self.0) {
            trace!(?err, "failed to remove socket, ignoring");
        }
    }
}

pub(crate) async fn run_unix(
    arbiter: Arbiter,
    name: &str,
    router: Router,
    addr: unix::net::SocketAddr,
) -> Result<()> {
    info!(?addr, "starting {name} server");

    let handle = Handle::new();
    arbiter.add_unix_handle(handle.clone()).await;

    let _guard = if let Some(path) = addr.as_pathname() {
        trace!(?addr, "removing socket");
        if let Err(err) = std::fs::remove_file(path) {
            trace!(?err, "failed to remove socket, ignoring");
        }
        Some(UnixSocketGuard(path.to_owned()))
    } else {
        None
    };
    axum_server::Server::bind(addr.clone())
        .acceptor(CatchPanicAcceptor::new(
            DefaultAcceptor::new(),
            arbiter.clone(),
        ))
        .handle(handle)
        .serve(router.into_make_service())
        .await?;

    Ok(())
}

/// Start a Unix socket server.
///
/// `name` is only used for observability purposes and should describe which module is starting the
/// server.
pub fn start_unix(
    tasks: &mut Tasks,
    name: &'static str,
    router: Router,
    addr: unix::net::SocketAddr,
) -> Result<()> {
    let arbiter = tasks.arbiter();
    tasks
        .build_task()
        .name(&format!("{}::run_unix({name}, {addr:?})", module_path!()))
        .spawn(run_unix(arbiter, name, router, addr))?;
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
        .acceptor(CatchPanicAcceptor::new(
            ProxyProtocolAcceptor::new().acceptor(TlsAcceptor::new(
                RustlsAcceptor::new(config).acceptor(DefaultAcceptor::new()),
            )),
            arbiter.clone(),
        ))
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
