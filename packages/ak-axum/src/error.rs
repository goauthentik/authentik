//! Custom error type for use in [`axum`] handlers.

use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
};
use eyre::Report;
use tracing::warn;

/// Custom error type for use in [`axum`] handlers, wrapping a [`Report`].
///
/// It implements [`IntoResponse`] and logs errors before returning a 502.
#[derive(Debug)]
pub struct AppError(pub Report);

impl<E> From<E> for AppError
where
    E: Into<Report>,
{
    fn from(err: E) -> Self {
        Self(err.into())
    }
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        warn!(error = ?self.0, "error occurred");
        (StatusCode::INTERNAL_SERVER_ERROR, "Something went wrong").into_response()
    }
}

/// Result type with [`AppError`].
pub type Result<T, E = AppError> = std::result::Result<T, E>;
