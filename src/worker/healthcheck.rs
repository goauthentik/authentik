use std::sync::Arc;

use ak_axum::{error::Result, router::wrap_router};
use ak_common::db;
use axum::{Router, extract::State, http::StatusCode, response::IntoResponse, routing::any};
use tracing::instrument;

use super::Workers;

#[instrument(skip_all)]
async fn health_ready(State(workers): State<Arc<Workers>>) -> Result<StatusCode> {
    if !workers.are_alive().await || sqlx::query("SELECT 1").execute(db::get()).await.is_err() {
        Ok(StatusCode::SERVICE_UNAVAILABLE)
    } else if workers.health_ready().await? {
        Ok(StatusCode::OK)
    } else {
        Ok(StatusCode::SERVICE_UNAVAILABLE)
    }
}

#[instrument(skip_all)]
async fn health_live(State(workers): State<Arc<Workers>>) -> Result<StatusCode> {
    if !workers.are_alive().await || sqlx::query("SELECT 1").execute(db::get()).await.is_err() {
        Ok(StatusCode::SERVICE_UNAVAILABLE)
    } else if workers.health_live().await? {
        Ok(StatusCode::OK)
    } else {
        Ok(StatusCode::SERVICE_UNAVAILABLE)
    }
}

async fn fallback() -> impl IntoResponse {
    StatusCode::OK
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
