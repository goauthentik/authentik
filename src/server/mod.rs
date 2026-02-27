use std::{sync::atomic::Ordering, time::Duration};

use argh::FromArgs;
use axum::{Router, body::Body, extract::Request, routing::any};
use axum_server::Handle;
use eyre::{Result, eyre};
use tokio::{signal::unix::SignalKind, sync::broadcast::error::RecvError, time::Instant};
use tower::ServiceExt;
use tracing::{info, warn};

use crate::{
    arbiter::{Arbiter, Tasks},
    config,
    server::gunicorn::{GUNICORN_READY, Gunicorn},
};

pub(crate) mod core;
mod gunicorn;
mod plain;
mod r#static;
mod tls;

#[derive(Debug, Default, FromArgs, PartialEq)]
/// Run the authentik server.
#[argh(subcommand, name = "server")]
pub(super) struct Cli {}

async fn watch_gunicorn(arbiter: Arbiter, mut gunicorn: Gunicorn) -> Result<()> {
    info!("starting gunicorn watcher");
    let mut signals_rx = arbiter.signals_subscribe();
    loop {
        tokio::select! {
            signal = signals_rx.recv() => {
                match signal {
                    Ok(signal) => {
                        if signal == SignalKind::user_defined1() {
                            info!("gunicorn notified us ready, marked ready for operation");
                            GUNICORN_READY.store(true, Ordering::Relaxed);
                            arbiter.mark_gunicorn_ready();
                        }
                    },
                    Err(RecvError::Lagged(_)) => continue,
                    Err(RecvError::Closed) => {
                        warn!("error receiving signals");
                        return Err(RecvError::Closed.into());
                    }
                }
            },
            _ = tokio::time::sleep(Duration::from_secs(1)), if !GUNICORN_READY.load(Ordering::Relaxed) => {
                // On some platforms the SIGUSR1 can be missed.
                // Fall back to probing the gunicorn unix socket and mark ready once it accepts connections.
                if Gunicorn::is_socket_ready().await {
                    info!("gunicorn socket is accepting connections, marked ready for operation");
                    GUNICORN_READY.store(true, Ordering::Relaxed);
                    arbiter.mark_gunicorn_ready();
                }
            },
            _ = tokio::time::sleep(Duration::from_secs(5)) => {
                if !gunicorn.is_alive().await {
                    return Err(eyre!("gunicorn has exited unexpectedly"));
                }
            },
            _ = arbiter.fast_shutdown() => {
                gunicorn.fast_shutdown().await?;
                return Ok(());
            },
            _ = arbiter.graceful_shutdown() => {
                gunicorn.graceful_shutdown().await?;
                return Ok(());
            },
        }
    }
}

async fn build_router() -> Router {
    let core_router = core::build_router().await;
    let proxy_router: Option<Router> = None;

    Router::new().fallback(any(|request: Request<Body>| async move {
        metrics::describe_histogram!(
            "authentik_main_request_duration",
            metrics::Unit::Seconds,
            "API request latencies in seconds"
        );
        let now = Instant::now();
        if let Some(proxy_router) = proxy_router
            && crate::proxy::can_handle(&request)
        {
            let res = proxy_router.oneshot(request).await;
            metrics::histogram!("authentik_main_request_duration", "dest" => "embedded_outpost")
                .record(now.elapsed());
            res
        } else {
            let res = core_router.oneshot(request).await;
            metrics::histogram!("authentik_main_request_duration", "dest" => "core")
                .record(now.elapsed());
            res
        }
    }))
}

pub(super) async fn run(_cli: Cli, tasks: &mut Tasks) -> Result<()> {
    let config = config::get();
    let arbiter = tasks.arbiter();

    let gunicorn = Gunicorn::new()?;

    let router = build_router().await;
    let tls_config = tls::make_initial_tls_config()?;

    tasks
        .build_task()
        .name(&format!("{}::tls::watch_tls_config", module_path!(),))
        .spawn(tls::watch_tls_config(arbiter.clone(), tls_config.clone()))?;

    for addr in config.listen.http.iter().copied() {
        let handle = Handle::new();
        arbiter.add_handle(handle.clone()).await;
        tasks
            .build_task()
            .name(&format!(
                "{}::plain::run_server_plain({})",
                module_path!(),
                addr
            ))
            .spawn(plain::run_server_plain(router.clone(), addr, handle))?;
    }

    for addr in config.listen.https.iter().copied() {
        let handle = Handle::new();
        arbiter.add_handle(handle.clone()).await;
        tasks
            .build_task()
            .name(&format!(
                "{}::tls::run_server_tls({})",
                module_path!(),
                addr
            ))
            .spawn(tls::run_server_tls(
                router.clone(),
                addr,
                tls_config.clone(),
                handle,
            ))?;
    }

    tasks
        .build_task()
        .name(&format!("{}::watch_gunicorn", module_path!()))
        .spawn(watch_gunicorn(arbiter, gunicorn))?;

    Ok(())
}
