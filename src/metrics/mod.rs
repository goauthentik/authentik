use std::{env::temp_dir, os::unix, sync::Arc, time::Duration};

use arc_swap::ArcSwapOption;
use axum::{Router, routing::any};
use eyre::Result;
use metrics_exporter_prometheus::{PrometheusBuilder, PrometheusHandle};

use crate::{
    arbiter::{Arbiter, Tasks},
    axum::{router::wrap_router, server},
    config,
};
#[cfg(feature = "core")]
use crate::{server::Server, worker::Workers};

mod handlers;

pub struct Metrics {
    prometheus: PrometheusHandle,
    #[cfg(feature = "core")]
    pub server: ArcSwapOption<Server>,
    #[cfg(feature = "core")]
    pub workers: ArcSwapOption<Workers>,
}

impl Metrics {
    fn new() -> Result<Self> {
        let prometheus = PrometheusBuilder::new()
            .with_recommended_naming(true)
            .install_recorder()?;
        Ok(Self {
            prometheus,
            #[cfg(feature = "core")]
            server: ArcSwapOption::empty(),
            #[cfg(feature = "core")]
            workers: ArcSwapOption::empty(),
        })
    }
}

async fn run_upkeep(arbiter: Arbiter, state: Arc<Metrics>) -> Result<()> {
    loop {
        tokio::select! {
            () = tokio::time::sleep(Duration::from_secs(5)) => {
                let state_clone = Arc::clone(&state);
                tokio::task::spawn_blocking(move || state_clone.prometheus.run_upkeep()).await?;
            },
            () = arbiter.shutdown() => return Ok(())
        }
    }
}

fn build_router(state: Arc<Metrics>) -> Router {
    wrap_router(
        Router::new()
            .fallback(any(handlers::metrics_handler))
            .with_state(state),
        true,
    )
}

pub fn run(tasks: &mut Tasks) -> Result<Arc<Metrics>> {
    let arbiter = tasks.arbiter();
    let metrics = Arc::new(Metrics::new()?);
    let router = build_router(Arc::clone(&metrics));

    tasks
        .build_task()
        .name(&format!("{}::run_upkeep", module_path!(),))
        .spawn(run_upkeep(arbiter, Arc::clone(&metrics)))?;

    for addr in config::get().listen.metrics.iter().copied() {
        server::start_plain(tasks, "metrics", router.clone(), addr)?;
    }

    server::start_unix(
        tasks,
        "metrics",
        router,
        unix::net::SocketAddr::from_pathname(temp_dir().join("authentik-metrics.sock"))?,
    )?;

    Ok(metrics)
}
