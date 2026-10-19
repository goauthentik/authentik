//! The processes that run authentik's Python applications for the server.
//!
//! The server starts this as a separate process, which loads the applications once and then
//! forks the processes that run them, so that those share what was loaded. It stays
//! single-threaded, as forking is only safe then. The forked processes all accept connections
//! on the same socket, which the server forwards requests to.

use std::{
    collections::HashMap, net::Ipv6Addr, os::unix::net::UnixListener, path::PathBuf, sync::Arc,
    time::Duration,
};

use ak_common::{config, tracing as ak_tracing};
use argh::FromArgs;
use axum::{
    Router,
    extract::{Request, State},
    http::{HeaderMap, StatusCode},
    response::{IntoResponse as _, Response},
};
use eyre::{Result, eyre};
use nix::{
    sys::{
        signal::{SigSet, Signal, kill},
        wait::{WaitPidFlag, WaitStatus, waitpid},
    },
    unistd::{Pid, getppid},
};
use pyo3::prelude::*;
use tokio::{
    signal::unix::{SignalKind, signal},
    time::interval,
};
use tracing::{error, info, warn};

use super::{
    asgi::{Asgi, Peer},
    core::websockets::is_websocket_upgrade,
    wsgi::Wsgi,
};

#[derive(Debug, FromArgs, PartialEq)]
/// Run the server's Python processes. The server starts this itself.
#[argh(subcommand, name = "server-prefork")]
pub(crate) struct Cli {
    /// the socket to accept connections on
    #[argh(positional)]
    socket_path: PathBuf,
}

pub(crate) fn run(cli: &Cli, tracing_crude: tracing::dispatcher::DefaultGuard) -> Result<()> {
    config::init()?;
    drop(tracing_crude);
    // ponytail: `listen.debug_tokio` makes this start a thread, which the forked processes
    // don't get. Install it after forking if it needs to work here.
    ak_tracing::install()?;
    // Waited for below rather than handled, which would need a thread
    let mut signals = SigSet::empty();
    for signal in [Signal::SIGTERM, Signal::SIGINT, Signal::SIGCHLD] {
        signals.add(signal);
    }
    signals.thread_block()?;

    crate::python::initialize()?;
    Python::attach(|py| {
        py.import("lifecycle.server")?
            .call_method0("preload")
            .map(drop)
    })?;

    // Only bound now, as the server takes connections being accepted to mean we're ready
    let _ = std::fs::remove_file(&cli.socket_path);
    let listener = UnixListener::bind(&cli.socket_path)?;

    let mut children = HashMap::new();
    for worker_id in 1..=config::get().web.workers.get() {
        children.insert(fork_worker(worker_id, &listener, signals)?, worker_id);
    }
    kill(getppid(), Signal::SIGUSR1)?;

    loop {
        let signal = signals.wait()?;
        if signal != Signal::SIGCHLD {
            info!(signal = signal.as_str(), "stopping server processes");
            for pid in children.keys() {
                let _ = kill(*pid, signal);
            }
            while let Ok(status) = waitpid(None, None) {
                if let Some(pid) = status.pid() {
                    children.remove(&pid);
                }
                if children.is_empty() {
                    break;
                }
            }
            return Ok(());
        }
        while let Ok(status) = waitpid(None, Some(WaitPidFlag::WNOHANG)) {
            let Some(pid) = status.pid() else {
                break;
            };
            if !matches!(status, WaitStatus::Exited(..) | WaitStatus::Signaled(..)) {
                continue;
            }
            let Some(worker_id) = children.remove(&pid) else {
                continue;
            };
            warn!(worker_id, ?status, "server process exited, restarting it");
            // So that a process failing right away doesn't make us fork in a tight loop
            std::thread::sleep(Duration::from_secs(1));
            children.insert(fork_worker(worker_id, &listener, signals)?, worker_id);
        }
    }
}

fn fork_worker(worker_id: usize, listener: &UnixListener, signals: SigSet) -> Result<Pid> {
    // Through Python, so that the interpreter is prepared for the fork
    let pid: i32 = Python::attach(|py| py.import("os")?.call_method0("fork")?.extract())?;
    if pid != 0_i32 {
        return Ok(Pid::from_raw(pid));
    }
    let result = signals
        .thread_unblock()
        .map_err(Into::into)
        .and_then(|()| worker(worker_id, listener));
    if let Err(err) = &result {
        error!(worker_id, ?err, "server process failed");
    }
    #[expect(
        clippy::exit,
        reason = "the forked process must not return to the loop forking it"
    )]
    std::process::exit(i32::from(result.is_err()));
}

struct App {
    asgi: Asgi,
    wsgi: Wsgi,
}

fn worker(worker_id: usize, listener: &UnixListener) -> Result<()> {
    // Don't outlive the process that forked us when it is killed
    #[cfg(target_os = "linux")]
    nix::sys::prctl::set_pdeathsig(Signal::SIGKILL)?;

    let (asgi, wsgi) = Asgi::start_worker(worker_id)?;
    let app = Arc::new(App {
        asgi,
        wsgi: Wsgi::new(wsgi, config::get().web.threads)?,
    });
    listener.set_nonblocking(true)?;
    let listener = listener.try_clone()?;

    tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()?
        .block_on(async {
            let listener = tokio::net::UnixListener::from_std(listener)?;
            let mut terminate = signal(SignalKind::terminate())?;
            let mut interrupt = signal(SignalKind::interrupt())?;
            let router = Router::new().fallback(handle).with_state(Arc::clone(&app));
            let serve = axum::serve(listener, router).with_graceful_shutdown(async move {
                terminate.recv().await;
            });
            let watch = async {
                let mut check = interval(Duration::from_secs(5));
                loop {
                    check.tick().await;
                    if !app.asgi.is_alive().await {
                        return;
                    }
                }
            };
            tokio::select! {
                res = serve => res?,
                _ = interrupt.recv() => {},
                () = watch => return Err(eyre!("the application's event loop has stopped")),
            }
            app.asgi.shutdown().await
        })
}

/// Only the server connects to us, which says who the request came from in these
fn peer(headers: &HeaderMap) -> Peer {
    let header = |name| headers.get(name)?.to_str().ok();
    Peer {
        client: header("x-forwarded-for")
            .and_then(|value| value.parse().ok())
            .unwrap_or_else(|| Ipv6Addr::LOCALHOST.into()),
        scheme: header("x-forwarded-proto").unwrap_or("http").to_owned(),
    }
}

async fn handle(State(app): State<Arc<App>>, request: Request) -> Response {
    let peer = peer(request.headers());
    let result = if is_websocket_upgrade(request.headers()) {
        app.asgi.websocket(request, &peer).await
    } else {
        app.wsgi.http(request, &peer).await
    };
    result.unwrap_or_else(|err| {
        warn!(?err, "failed to handle request");
        StatusCode::INTERNAL_SERVER_ERROR.into_response()
    })
}
