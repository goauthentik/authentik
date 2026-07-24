use std::sync::Arc;

use ak_axum::{error::Result, router::wrap_router};
use ak_common::db;
use axum::{Router, extract::State, http::StatusCode, routing::any};
use tracing::{instrument, warn};

use super::Workers;

#[instrument(skip_all)]
async fn health_ready(State(workers): State<Arc<Workers>>) -> Result<StatusCode> {
    if !workers.are_alive().await {
        warn!("workers detected as not alive");
        return Ok(StatusCode::SERVICE_UNAVAILABLE);
    }

    if let Err(err) = sqlx::query("SELECT 1").execute(db::get()).await {
        warn!(?err, "failed to check db health");
        return Ok(StatusCode::SERVICE_UNAVAILABLE);
    }

    match workers.health_ready().await {
        Ok(true) => {}
        Ok(false) => {
            warn!("workers responded not ready");
            return Ok(StatusCode::SERVICE_UNAVAILABLE);
        }
        Err(err) => {
            warn!(?err, "failed to check workers health readiness");
            return Ok(StatusCode::SERVICE_UNAVAILABLE);
        }
    }

    Ok(StatusCode::OK)
}

#[instrument(skip_all)]
async fn health_live(State(workers): State<Arc<Workers>>) -> Result<StatusCode> {
    if !workers.are_alive().await {
        warn!("workers detected as not alive");
        return Ok(StatusCode::SERVICE_UNAVAILABLE);
    }

    match workers.health_live().await {
        Ok(true) => {}
        Ok(false) => {
            warn!("workers responded not live");
            return Ok(StatusCode::SERVICE_UNAVAILABLE);
        }
        Err(err) => {
            warn!(?err, "failed to check workers health liveness");
            return Ok(StatusCode::SERVICE_UNAVAILABLE);
        }
    }

    Ok(StatusCode::OK)
}

async fn fallback() -> StatusCode {
    StatusCode::NOT_FOUND
}

pub(super) fn build_router(workers: Arc<Workers>) -> Router {
    wrap_router(
        Router::new()
            .route("/-/heath/ready/", any(health_ready))
            .route("/-/heath/live/", any(health_live))
            .fallback(fallback)
            .with_state(workers),
        true,
    )
}
