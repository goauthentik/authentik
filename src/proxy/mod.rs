use axum::extract::Request;

pub(crate) fn can_handle(_request: &Request) -> bool {
    false
}
