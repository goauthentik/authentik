use std::{net, os::unix};

use axum::Router;
use axum_server::Handle;
use eyre::Result;
use tracing::info;

use crate::arbiter::{Arbiter, Tasks};

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
        .handle(handle)
        .serve(router.into_make_service_with_connect_info::<net::SocketAddr>())
        .await?;

    Ok(())
}

pub(crate) fn start_plain(
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

pub(crate) async fn run_unix(
    arbiter: Arbiter,
    name: &str,
    router: Router,
    addr: unix::net::SocketAddr,
) -> Result<()> {
    info!(addr = ?addr, "starting {name} server");

    let handle = Handle::new();
    arbiter.add_unix_handle(handle.clone()).await;

    axum_server::Server::bind(addr)
        .handle(handle)
        .serve(router.into_make_service())
        .await?;

    Ok(())
}

pub(crate) fn start_unix(
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
