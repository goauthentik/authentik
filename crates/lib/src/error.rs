use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
};
use tracing::warn;

#[derive(Debug)]
pub struct Error(eyre::Error);

impl<E> From<E> for Error
where
    E: Into<eyre::Error>,
{
    fn from(err: E) -> Self {
        Self(err.into())
    }
}

impl IntoResponse for Error {
    fn into_response(self) -> Response {
        warn!("Error occured: {:?}", self.0);
        (StatusCode::INTERNAL_SERVER_ERROR, "Something went wrong").into_response()
    }
}

pub type Result<T, E = Error> = core::result::Result<T, E>;
