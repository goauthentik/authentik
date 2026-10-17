use std::{net::Ipv6Addr, num::NonZeroUsize, os::unix, sync::Arc};

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
    http::StatusCode,
    middleware::from_fn,
    response::Response,
    routing::any,
};
use eyre::{Result, eyre};
use rustls::sign::CertifiedKey;
use tokio::{
    task::spawn_blocking,
    time::{Duration, Instant, interval},
};
use tower::ServiceExt as _;
use tracing::{info, instrument, trace, warn};

use crate::{
    brands::tls::BrandCertResolver,
    outpost::{self, proxy::ProxyOutpost},
    worker::Workers,
};

mod asgi;
mod core;
mod r#static;
mod tls;
mod wsgi;

/// How many Python threads WSGI requests (see `wsgi::Wsgi::http`) run on.
///
/// Each of those threads holds one Postgres connection open for the life of its request —
/// `postgresql.conn_max_age` defaults to `0`, so Django opens a fresh connection per request
/// rather than reusing one — so this number also caps how many connections the core server
/// opens at once. A default Postgres install caps `max_connections` at 100 total, shared with
/// the worker process, migrations, `psql` sessions, and everything else talking to the same
/// database, so this deliberately stays well under that instead of scaling unbounded with core
/// count the way tokio's default blocking pool (up to 512 threads) would.
///
/// `web.max_blocking_threads` overrides this for deployments with a larger Postgres instance
/// (e.g. pooled through pgbouncer, or with `max_connections` raised) in front of them.
pub(crate) fn blocking_thread_count() -> NonZeroUsize {
    if let Some(configured) = config::get().web.max_blocking_threads {
        return configured;
    }
    let cores = std::thread::available_parallelism().map_or(1, NonZeroUsize::get);
    // 4 threads/core covers the gaps while one request waits on the database or an upstream
    // IdP, without being able to open more connections than a default Postgres comfortably
    // tolerates alongside everything else using it.
    NonZeroUsize::new((cores * 4).clamp(8, 32)).expect("clamped to at least 8, so non-zero")
}

#[derive(Debug, Default, FromArgs, PartialEq, Eq)]
/// Run the authentik server.
#[argh(subcommand, name = "server")]
#[expect(
    clippy::empty_structs_with_brackets,
    reason = "argh doesn't support unit structs"
)]
pub(crate) struct Cli {}

pub(crate) fn socket_path() -> std::path::PathBuf {
    std::env::temp_dir().join("authentik.sock")
}

#[derive(Debug)]
pub(crate) struct Server {
    /// The ASGI application, once it has loaded. Only used for websockets now; ordinary
    /// HTTP requests go through `wsgi` instead, see `super::wsgi`.
    asgi: ArcSwapOption<asgi::Asgi>,
    /// The WSGI application, once it has loaded.
    wsgi: ArcSwapOption<wsgi::Wsgi>,
    pub(crate) workers: ArcSwapOption<Workers>,
    proxy_outpost: Arc<ArcSwapOption<ProxyOutpost>>,
    brand_cert_resolver: ArcSwapOption<BrandCertResolver>,
    fallback_cert: Arc<CertifiedKey>,
}

impl Server {
    fn new() -> Result<Self> {
        Ok(Self {
            asgi: ArcSwapOption::empty(),
            wsgi: ArcSwapOption::empty(),
            workers: ArcSwapOption::empty(),
            proxy_outpost: Arc::new(ArcSwapOption::empty()),
            brand_cert_resolver: ArcSwapOption::empty(),
            fallback_cert: Arc::new(self_signed::generate_certifiedkey()?),
        })
    }

    async fn is_alive(&self) -> bool {
        match self.asgi.load_full() {
            Some(asgi) => asgi.is_alive().await,
            // Still loading
            None => true,
        }
    }

    /// Send a request for the application to the application.
    async fn get(&self, path: &str) -> Result<StatusCode> {
        let asgi = self
            .asgi
            .load_full()
            .ok_or_else(|| eyre!("server is not ready"))?;
        let request = Request::builder()
            .uri(path)
            .header("host", "localhost")
            .body(Body::empty())?;
        let peer = asgi::Peer {
            client: Ipv6Addr::LOCALHOST.into(),
            scheme: "http".to_owned(),
        };
        Ok(asgi.http(request, &peer).await?.status())
    }

    #[instrument(skip(self))]
    pub(crate) async fn health_live(&self) -> Result<bool> {
        trace!("sending health live request to server");
        Ok(self
            .get("/-/health/live/")
            .await
            .inspect_err(|err| warn!(?err, "failed to send health live request to server"))?
            .is_success())
    }

    #[instrument(skip(self))]
    pub(crate) async fn health_ready(&self) -> Result<bool> {
        trace!("sending health ready request to server");
        Ok(self
            .get("/-/health/ready/")
            .await
            .inspect_err(|err| warn!(?err, "failed to send health ready request to server"))?
            .is_success())
    }

    #[instrument(skip(self))]
    pub(crate) async fn notify_metrics(&self) -> Result<()> {
        trace!("sending metrics request to server");
        self.get("/-/metrics/")
            .await
            .inspect_err(|err| warn!(?err, "failed to send metrics request to server"))?;
        Ok(())
    }
}

async fn watch_server(arbiter: Arbiter, server: Arc<Server>) -> Result<()> {
    info!("starting server");
    let (asgi, wsgi_application) = tokio::select! {
        loaded = spawn_blocking(asgi::Asgi::load) => loaded??,
        () = arbiter.shutdown() => return Ok(()),
    };
    let asgi = Arc::new(asgi);
    server.asgi.store(Some(Arc::clone(&asgi)));
    server.wsgi.store(Some(Arc::new(wsgi::Wsgi::new(
        wsgi_application,
        blocking_thread_count(),
    )?)));
    info!("server loaded, marked ready for operation");
    arbiter.send_event(Event::GunicornIsReady)?;

    let mut check_interval = interval(Duration::from_secs(5));
    loop {
        tokio::select! {
            _ = check_interval.tick() => {
                if !asgi.is_alive().await {
                    arbiter.do_fast_shutdown().await;
                    return Err(eyre!("the server has exited unexpectedly"));
                }
            },
            () = arbiter.shutdown() => {
                info!("shutting down server");
                return asgi.shutdown().await;
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

    // The embedded outpost is only populated once the server is ready, so this is
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

    let server = Arc::new(Server::new()?);

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
        info!("waiting for the server to be ready before starting embedded outpost");
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
