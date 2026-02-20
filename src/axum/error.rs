use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
};
use eyre::Report;
use tracing::warn;

#[derive(Debug)]
pub(crate) struct AppError(pub(crate) Report);

impl<E> From<E> for AppError
where E: Into<Report>
{
    fn from(err: E) -> Self {
        Self(err.into())
    }
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        warn!("Error occured: {:?}", self.0);
        (StatusCode::INTERNAL_SERVER_ERROR, "Something went wrong").into_response()
    }
}

pub(crate) type Result<T, E = AppError> = core::result::Result<T, E>;
