use std::{
    env::temp_dir,
    os::unix,
    path::PathBuf,
    process::Stdio,
    sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
    },
};

use ak_axum::{
    extract::{
        host::{Host, host_middleware},
        trusted_proxy::trusted_proxy_middleware,
    },
    router::make_request_body_limit_layer,
};
use ak_common::{Arbiter, Event, Tasks, config, tls::self_signed};
use arc_swap::ArcSwapOption;
use argh::FromArgs;
use axum::{
    Router,
    body::Body,
    extract::{Request, State},
    http::{StatusCode, header::HOST},
    middleware::from_fn,
    response::Response,
    routing::any,
};
use eyre::{Result, eyre};
use hyper_unix_socket::UnixSocketConnector;
use hyper_util::{client::legacy::Client, rt::TokioExecutor};
use nix::{
    sys::signal::{Signal, kill},
    unistd::Pid,
};
use rustls::sign::CertifiedKey;
use tokio::{
    net::UnixStream,
    process::{Child, Command},
    signal::unix::SignalKind,
    sync::Mutex,
    time::{Duration, Instant, interval},
};
use tower::ServiceExt as _;
use tracing::{debug, info, instrument, trace, warn};

use crate::{
    brands::tls::BrandCertResolver,
    outpost::{self, proxy::ProxyOutpost},
    worker::Workers,
};

mod core;
mod r#static;
mod tls;

#[derive(Debug, Default, FromArgs, PartialEq, Eq)]
/// Run the authentik server.
#[argh(subcommand, name = "server")]
#[expect(
    clippy::empty_structs_with_brackets,
    reason = "argh doesn't support unit structs"
)]
pub(crate) struct Cli {}

pub(super) static GUNICORN_READY: AtomicBool = AtomicBool::new(false);

pub(crate) type ServerClient = Client<UnixSocketConnector<PathBuf>, Body>;

/// How long uvicorn keeps an idle connection open. Match `keepalive` in
/// lifecycle/gunicorn.conf.py.
const GUNICORN_KEEPALIVE: Duration = Duration::from_secs(5);

/// Reusing a connection uvicorn is closing resets the request after it was
/// sent, and the client gets a 503. Drop idle connections a second before
/// uvicorn does, leaving room for a stalled event loop on either side.
const UPSTREAM_POOL_IDLE_TIMEOUT: Duration =
    GUNICORN_KEEPALIVE.saturating_sub(Duration::from_secs(1));

fn upstream_client(socket_path: PathBuf) -> ServerClient {
    Client::builder(TokioExecutor::new())
        .pool_idle_timeout(UPSTREAM_POOL_IDLE_TIMEOUT)
        .set_host(false)
        .build(UnixSocketConnector::new(socket_path))
}

pub(crate) fn socket_path() -> PathBuf {
    temp_dir().join("authentik.sock")
}

/// Returns `true` when `err` (or any error in its source chain) is an
/// `io::Error` with `ErrorKind::NotFound`
pub(crate) fn is_connect_not_found(err: &dyn std::error::Error) -> bool {
    let mut source = err.source();
    while let Some(e) = source {
        if let Some(io_err) = e.downcast_ref::<std::io::Error>()
            && io_err.kind() == std::io::ErrorKind::NotFound
        {
            return true;
        }
        source = e.source();
    }
    false
}

#[derive(Debug)]
pub(crate) struct Server {
    gunicorn: Mutex<Child>,
    socket_path: PathBuf,
    pub(crate) client: ServerClient,
    /// Used to retry requests that failed on a pooled connection, see [`core::send_to_server`].
    retry_client: ServerClient,
    pub(crate) workers: ArcSwapOption<Workers>,
    proxy_outpost: Arc<ArcSwapOption<ProxyOutpost>>,
    brand_cert_resolver: ArcSwapOption<BrandCertResolver>,
    fallback_cert: Arc<CertifiedKey>,
}

impl Server {
    fn new(socket_path: PathBuf) -> Result<Self> {
        info!("starting server");

        let gunicorn = Command::new("gunicorn")
            .args([
                "--bind",
                &format!("unix://{}", socket_path.display()),
                "-c",
                "./lifecycle/gunicorn.conf.py",
                "authentik.root.asgi:application",
            ])
            .kill_on_drop(true)
            .stdin(Stdio::null())
            .stdout(Stdio::inherit())
            .stderr(Stdio::inherit())
            .spawn()?;

        // Keeps no idle connections, so a retry always gets a new one.
        let retry_client = Client::builder(TokioExecutor::new())
            .pool_max_idle_per_host(0)
            .set_host(false)
            .build(UnixSocketConnector::new(socket_path.clone()));

        Ok(Self {
            gunicorn: Mutex::new(gunicorn),
            client: upstream_client(socket_path.clone()),
            retry_client,
            socket_path,
            workers: ArcSwapOption::empty(),
            proxy_outpost: Arc::new(ArcSwapOption::empty()),
            brand_cert_resolver: ArcSwapOption::empty(),
            fallback_cert: Arc::new(self_signed::generate_certifiedkey()?),
        })
    }

    async fn shutdown(&self, signal: Signal) -> Result<()> {
        trace!(
            signal = signal.as_str(),
            "sending shutdown signal to server"
        );
        let mut gunicorn = self.gunicorn.lock().await;
        if let Some(id) = gunicorn.id() {
            kill(Pid::from_raw(id.cast_signed()), signal)?;
        }
        gunicorn.wait().await?;
        drop(gunicorn);
        Ok(())
    }

    async fn graceful_shutdown(&self) -> Result<()> {
        info!("gracefully shutting down server");
        self.shutdown(Signal::SIGTERM).await
    }

    async fn fast_shutdown(&self) -> Result<()> {
        info!("immediately shutting down server");
        self.shutdown(Signal::SIGINT).await
    }

    async fn is_alive(&self) -> bool {
        let try_wait = self.gunicorn.lock().await.try_wait();
        match try_wait {
            Ok(Some(code)) => {
                warn!(?code, "server has exited");
                false
            }
            Ok(None) => true,
            Err(err) => {
                warn!(
                    ?err,
                    "failed to check the status of server process, ignoring"
                );
                true
            }
        }
    }

    async fn is_socket_ready(&self) -> bool {
        let result = UnixStream::connect(&self.socket_path).await;
        trace!(?result, "checking if server socket is ready");
        result.is_ok()
    }

    #[instrument(skip(self))]
    pub(crate) async fn health_live(&self) -> Result<bool> {
        trace!("sending health live request to server");
        let req = Request::builder()
            .method("GET")
            .uri("http://localhost:8000/-/health/live/")
            .header(HOST, "localhost")
            .body(Body::empty())?;
        Ok(self
            .client
            .request(req)
            .await
            .inspect_err(|err| {
                if is_connect_not_found(err) {
                    debug!(?err, "upstream socket not yet ready (health live)");
                } else {
                    warn!(?err, "failed to send health live request to server");
                }
            })?
            .status()
            .is_success())
    }

    #[instrument(skip(self))]
    pub(crate) async fn health_ready(&self) -> Result<bool> {
        trace!("sending health ready request to server");
        let req = Request::builder()
            .method("GET")
            .uri("http://localhost:8000/-/health/ready/")
            .header(HOST, "localhost")
            .body(Body::empty())?;
        Ok(self
            .client
            .request(req)
            .await
            .inspect_err(|err| warn!(?err, "failed to send health ready request to server"))?
            .status()
            .is_success())
    }

    #[instrument(skip(self))]
    pub(crate) async fn notify_metrics(&self) -> Result<()> {
        trace!("sending metrics request to server");
        let req = Request::builder()
            .method("GET")
            .uri("http://localhost:8000/-/metrics/")
            .header(HOST, "localhost")
            .body(Body::empty())?;
        self.client
            .request(req)
            .await
            .inspect_err(|err| warn!(?err, "failed to send metrics request to server"))?;
        Ok(())
    }
}

async fn watch_server(arbiter: Arbiter, server: Arc<Server>) -> Result<()> {
    info!("starting server watcher");
    let mut events_rx = arbiter.events_subscribe();
    let mut check_interval = interval(Duration::from_secs(5));
    let mut start_interval = interval(Duration::from_secs(1));

    loop {
        tokio::select! {
            event = events_rx.recv() => {
                if let Ok(Event::Signal(signal)) = event
                    && signal == SignalKind::user_defined1()
                    && !GUNICORN_READY.load(Ordering::Relaxed)
                {
                    info!("server notified us ready, marked ready for operation");
                    GUNICORN_READY.store(true, Ordering::Relaxed);
                    arbiter.send_event(Event::GunicornIsReady)?;
                }
            },
            _ = start_interval.tick(), if !GUNICORN_READY.load(Ordering::Relaxed) => {
                if server.is_socket_ready().await {
                    info!("server socket is accepting connections, marked ready for operation");
                    GUNICORN_READY.store(true, Ordering::Relaxed);
                    arbiter.send_event(Event::GunicornIsReady)?;
                }
            },
            _ = check_interval.tick() => {
                if !server.is_alive().await {
                    arbiter.do_fast_shutdown().await;
                    return Err(eyre!("the server has exited unexpectedly"));
                }
            },
            () = arbiter.fast_shutdown() => {
                server.fast_shutdown().await?;
                return Ok(());
            }
            () = arbiter.graceful_shutdown() => {
                server.graceful_shutdown().await?;
                return Ok(());
            }
        }
    }
}

async fn route_core_and_outpost(
    State((core_router, proxy_router, proxy_outpost)): State<(
        Router,
        Router,
        Arc<ArcSwapOption<ProxyOutpost>>,
    )>,
    Host(host): Host,
    mut request: Request,
) -> Response {
    let start = Instant::now();

    // The embedded outpost is only populated once gunicorn is ready, so this is
    // `None` during startup and every request naturally falls through to core.
    let app = proxy_outpost
        .load_full()
        .and_then(|outpost| outpost.app_for_request(&host, request.uri()));

    let (router, dest) = match app {
        Some(app) => {
            // The proxy router reads the resolved application from the request
            // extensions, so we don't look it up a second time.
            request.extensions_mut().insert(app);
            (proxy_router, "embedded_outpost")
        }
        None => (core_router, "core"),
    };

    let response = router.oneshot(request).await.expect("infallible");
    metrics::histogram!("authentik_main_request_duration", "dest" => dest)
        .record(start.elapsed().as_secs_f64());
    response
}

fn build_router(server: &Arc<Server>) -> Result<Router> {
    let core_router = core::build_router(server)?;
    let proxy_router = outpost::proxy::embedded_router();

    metrics::describe_histogram!(
        "authentik_main_request_duration",
        metrics::Unit::Seconds,
        "API request latencies in seconds"
    );

    let router = if config::get().outposts.disable_embedded_outpost {
        Router::new()
    } else {
        Router::new().route("/outpost.goauthentik.io/ping", any(StatusCode::NO_CONTENT))
    };

    Ok(router
        .fallback(any(route_core_and_outpost))
        .with_state((core_router, proxy_router, Arc::clone(&server.proxy_outpost)))
        .layer(from_fn(host_middleware))
        .layer(from_fn(trusted_proxy_middleware))
        .layer(make_request_body_limit_layer()))
}

pub(crate) async fn start(_cli: Cli, tasks: &mut Tasks) -> Result<Arc<Server>> {
    let arbiter = tasks.arbiter();
    let mut events_rx = arbiter.events_subscribe();

    let server = Arc::new(Server::new(temp_dir().join("authentik-gunicorn.sock"))?);

    tasks
        .build_task()
        .name(&format!("{}::watch_server", module_path!()))
        .spawn(watch_server(arbiter.clone(), Arc::clone(&server)))?;

    let router = build_router(&server)?;

    for addr in config::get().listen.http.iter().copied() {
        ak_axum::server::start_plain(tasks, "server", router.clone(), addr)?;
    }

    let tls_config = tls::make_initial_tls_config(Arc::clone(&server));
    for addr in config::get().listen.https.iter().copied() {
        ak_axum::server::start_tls(tasks, "server", router.clone(), addr, tls_config.clone())?;
    }
    tasks
        .build_task()
        .name(&format!("{}::tls::watch_tls_config", module_path!()))
        .spawn(tls::watch_tls_config(
            arbiter.clone(),
            tls_config,
            Arc::clone(&server),
        ))?;

    ak_axum::server::start_unix(
        tasks,
        "server",
        router,
        unix::net::SocketAddr::from_pathname(socket_path())?,
    )?;

    if !config::get().outposts.disable_embedded_outpost {
        info!("waiting for gunicorn to be ready before starting embedded outpost");
        loop {
            tokio::select! {
                event = events_rx.recv() => {
                    if event == Ok(Event::GunicornIsReady) {
                        break;
                    }
                },
                () = arbiter.shutdown() => {
                    warn!("we were told to shutdown before starting the embedded outpost");
                    return Ok(server);
                },
            }
        }

        info!("starting embedded outpost");
        let proxy_outpost = tokio::select! {
            res = outpost::start::<ProxyOutpost>(outpost::proxy::Cli::default(), tasks, None) => res?,
            () = arbiter.shutdown() => {
                warn!("we were told to shutdown before starting the embedded outpost");
                return Ok(server);
            },
        };
        server.proxy_outpost.store(Some(proxy_outpost));
    }

    Ok(server)
}

#[cfg(test)]
mod tests {
    use std::sync::atomic::AtomicUsize;

    use http_body_util::BodyExt as _;
    use tempfile::TempDir;
    use tokio::{
        io::{AsyncReadExt as _, AsyncWriteExt as _},
        net::UnixListener,
        time::sleep,
    };

    use super::*;

    /// Stands in for uvicorn: answers every request on a connection and keeps
    /// it open. Returns how many connections it accepted.
    fn spawn_upstream(socket_path: &std::path::Path) -> Arc<AtomicUsize> {
        let listener = UnixListener::bind(socket_path).expect("failed to bind upstream socket");
        let accepted = Arc::new(AtomicUsize::new(0));
        let counter = Arc::clone(&accepted);

        tokio::spawn(async move {
            loop {
                let (mut stream, _) = listener.accept().await.expect("failed to accept");
                counter.fetch_add(1, Ordering::SeqCst);
                tokio::spawn(async move {
                    let mut request = Vec::new();
                    let mut buf = [0_u8; 1024];
                    loop {
                        let read = stream.read(&mut buf).await.expect("failed to read");
                        if read == 0 {
                            return;
                        }
                        request.extend_from_slice(&buf[..read]);
                        if request.ends_with(b"\r\n\r\n") {
                            request.clear();
                            stream
                                .write_all(b"HTTP/1.1 200 OK\r\ncontent-length: 0\r\n\r\n")
                                .await
                                .expect("failed to write response");
                        }
                    }
                });
            }
        });

        accepted
    }

    async fn get(client: &ServerClient) {
        let request = Request::builder()
            .uri("http://localhost:8000/")
            .body(Body::empty())
            .expect("failed to build request");
        let response = client.request(request).await.expect("request failed");
        response
            .into_body()
            .collect()
            .await
            .expect("failed to read body");
    }

    /// Uvicorn may already be closing a connection that has been idle for
    /// almost its whole keep-alive, so the client must not pick it up again.
    #[tokio::test]
    async fn upstream_client_does_not_reuse_connections_uvicorn_is_closing() {
        let dir = TempDir::new().expect("failed to create temp dir");
        let socket_path = dir.path().join("authentik.sock");
        let accepted = spawn_upstream(&socket_path);
        let client = upstream_client(socket_path);

        get(&client).await;
        sleep(GUNICORN_KEEPALIVE.saturating_sub(Duration::from_millis(200))).await;
        get(&client).await;

        assert_eq!(accepted.load(Ordering::SeqCst), 2);
    }

    /// Back-to-back requests still share a connection. This also shows the
    /// upstream above tells reuse apart from new connections.
    #[tokio::test]
    async fn upstream_client_reuses_fresh_connections() {
        let dir = TempDir::new().expect("failed to create temp dir");
        let socket_path = dir.path().join("authentik.sock");
        let accepted = spawn_upstream(&socket_path);
        let client = upstream_client(socket_path);

        get(&client).await;
        get(&client).await;

        assert_eq!(accepted.load(Ordering::SeqCst), 1);
    }
}
