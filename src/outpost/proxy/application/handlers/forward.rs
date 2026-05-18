use std::sync::Arc;

use ak_axum::error::Result;
use axum::{
    extract::{Request, State},
    response::Response,
};
use tracing::instrument;

use crate::outpost::proxy::application::Application;

#[instrument(skip_all)]
pub(crate) async fn handle_caddy(
    State(_app): State<Arc<Application>>,
    _request: Request,
) -> Result<Response> {
    todo!()
}

#[instrument(skip_all)]
pub(crate) async fn handle_envoy(
    State(_app): State<Arc<Application>>,
    _request: Request,
) -> Result<Response> {
    todo!()
}

#[instrument(skip_all)]
pub(crate) async fn handle_nginx(
    State(_app): State<Arc<Application>>,
    _request: Request,
) -> Result<Response> {
    todo!()
}

#[instrument(skip_all)]
pub(crate) async fn handle_traefik(
    State(_app): State<Arc<Application>>,
    _request: Request,
) -> Result<Response> {
    todo!()
}
