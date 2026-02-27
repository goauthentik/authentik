use std::{net::SocketAddr, sync::Arc, time::Duration};

use axum::{Router, routing::any};
use axum_server::Handle;
use eyre::Result;
use metrics_exporter_prometheus::{PrometheusBuilder, PrometheusHandle};
use tower_http::trace::{DefaultMakeSpan, DefaultOnRequest, DefaultOnResponse, TraceLayer};
use tracing::{Level, info};

use crate::{
    arbiter::{Arbiter, Tasks},
    config,
};

mod handlers;

struct AppState {
    prometheus: PrometheusHandle,
    #[cfg(feature = "core")]
    metrics_key: String,
    #[cfg(feature = "core")]
    _metrics_file: tempfile::NamedTempFile,
}

impl AppState {
    async fn new() -> Result<Self> {
        let prometheus = PrometheusBuilder::new()
            .with_recommended_naming(true)
            .install_recorder()?;
        #[cfg(not(feature = "core"))]
        {
            Ok(Self { prometheus })
        }
        #[cfg(feature = "core")]
        {
            use std::{fs::Permissions, os::unix::fs::PermissionsExt};

            use rand::distr::SampleString;

            let metrics_key = rand::distr::Alphanumeric.sample_string(&mut rand::rng(), 64);
            let metrics_file = tempfile::Builder::new()
                .prefix("authentik-metrics-gunicorn")
                .suffix(".key")
                .rand_bytes(0)
                .permissions(Permissions::from_mode(0o600))
                .tempfile()?;
            tokio::fs::write(&metrics_file, &metrics_key).await?;
            Ok(Self {
                prometheus,
                metrics_key,
                _metrics_file: metrics_file,
            })
        }
    }
}

async fn run_upkeep(arbiter: Arbiter, state: Arc<AppState>) -> Result<()> {
    loop {
        tokio::select! {
            _ = tokio::time::sleep(Duration::from_secs(5)) => {
                state.prometheus.run_upkeep();
            },
            _ = arbiter.shutdown() => return Ok(())
        }
    }
}

fn build_router(state: Arc<AppState>) -> Router {
    Router::new()
        .fallback(any(handlers::metrics_handler))
        .layer(
            // TODO: refine this, probably extract it to its own thing to be used with the proxy
            // outpost
            TraceLayer::new_for_http()
                .make_span_with(DefaultMakeSpan::new().level(Level::INFO))
                .on_request(DefaultOnRequest::new().level(Level::INFO))
                .on_response(DefaultOnResponse::new().level(Level::INFO)),
        )
        .with_state(state)
}

async fn run_server(router: Router, addr: SocketAddr, handle: Handle<SocketAddr>) -> Result<()> {
    info!(addr = addr.to_string(), "starting metrics server");
    axum_server::Server::bind(addr)
        .handle(handle)
        .serve(router.into_make_service_with_connect_info::<SocketAddr>())
        .await?;

    Ok(())
}

pub(super) async fn run(tasks: &mut Tasks) -> Result<()> {
    let arbiter = tasks.arbiter();
    let state = Arc::new(AppState::new().await?);
    let router = build_router(state.clone());

    tasks
        .build_task()
        .name(&format!("{}::metrics::run_upkeep", module_path!(),))
        .spawn(run_upkeep(arbiter.clone(), state.clone()))?;

    for addr in config::get().listen.metrics.iter().copied() {
        let handle = Handle::new();
        arbiter.add_handle(handle.clone()).await;
        tasks
            .build_task()
            .name(&format!(
                "{}::metrics::run_server({})",
                module_path!(),
                addr
            ))
            .spawn(run_server(router.clone(), addr, handle))?;
    }

    Ok(())
}
