use axum::extract::Request;

pub fn can_handle(_request: &Request) -> bool {
    false
}
