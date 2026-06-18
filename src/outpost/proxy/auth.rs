//! Resolving claims from the session, the auth cache, or a bearer token.

use axum::http::HeaderMap;
use axum::http::header::AUTHORIZATION;
use tracing::warn;

use crate::outpost::proxy::application::Application;
use crate::outpost::proxy::{backchannel, claims::Claims};

/// Extract the bearer token from an `Authorization` header value.
pub(crate) fn bearer_token(value: &str) -> Option<&str> {
    const PREFIX: &str = "Bearer ";
    if value.get(..PREFIX.len())?.eq_ignore_ascii_case(PREFIX) {
        value.get(PREFIX.len()..)
    } else {
        None
    }
}

impl Application {
    /// The raw `Authorization` header value, used as the auth cache key.
    pub(super) fn authorization_header(headers: &HeaderMap) -> Option<&str> {
        headers.get(AUTHORIZATION)?.to_str().ok()
    }

    /// Look up previously-resolved claims for an `Authorization` header.
    pub(super) async fn cached_claims(&self, key: &str) -> Option<Claims> {
        self.auth_cache.get(key).await
    }

    /// Cache resolved claims for an `Authorization` header (first write wins).
    pub(super) async fn cache_claims(&self, key: &str, claims: &Claims) {
        if self.auth_cache.get(key).await.is_none() {
            self.auth_cache.insert(key.to_owned(), claims.clone()).await;
        }
    }

    /// Resolve claims by introspecting a bearer token.
    pub(super) async fn attempt_bearer_auth(&self, token: &str) -> Option<Claims> {
        let client_id = self.provider.client_id.as_deref()?;
        let client_secret = self.provider.client_secret.as_deref()?;
        backchannel::introspect_token(
            &self.client,
            &self.endpoint.token_introspection,
            self.token_host.as_deref(),
            client_id,
            client_secret,
            token,
        )
        .await
        .inspect_err(|err| warn!(?err, "bearer introspection failed"))
        .ok()
        .flatten()
    }
}

#[cfg(test)]
mod tests {
    use super::bearer_token;

    #[test]
    fn extracts_bearer_token() {
        assert_eq!(bearer_token("Bearer abc123"), Some("abc123"));
        // The scheme is case-insensitive.
        assert_eq!(bearer_token("bearer abc123"), Some("abc123"));
        assert_eq!(bearer_token("Basic abc123"), None);
        assert_eq!(bearer_token("Bearer"), None);
        assert_eq!(bearer_token(""), None);
    }
}
