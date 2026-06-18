//! Resolving claims from the session, the auth cache, or a bearer token.

use axum::http::HeaderMap;
use axum::http::header::AUTHORIZATION;
use eyre::{Result, eyre};
use tracing::warn;

use crate::outpost::proxy::application::Application;
use crate::outpost::proxy::{backchannel, claims::Claims, token};

/// Username that signals the password is a bearer token to introspect.
const JWT_USERNAME: &str = "goauthentik.io/token";

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

    /// Verify a signed token (HS256 by client secret, else RS256 via JWKS).
    pub(super) async fn verify_token(&self, token: &str) -> Result<Claims> {
        let client_id = self
            .provider
            .client_id
            .as_deref()
            .ok_or_else(|| eyre!("provider has no client id"))?;
        let supports_hs256 = self
            .provider
            .oidc_configuration
            .id_token_signing_alg_values_supported
            .iter()
            .any(|alg| alg == "HS256");
        if supports_hs256 {
            let client_secret = self
                .provider
                .client_secret
                .as_deref()
                .ok_or_else(|| eyre!("provider has no client secret"))?;
            token::verify_hs256(token, client_secret, &self.endpoint.issuer, client_id)
        } else {
            let jwks = backchannel::fetch_jwks(&self.client, &self.endpoint.jwks_uri).await?;
            token::verify_rs256(token, &jwks, &self.endpoint.issuer, client_id)
        }
    }

    /// Resolve claims from HTTP basic auth: a `goauthentik.io/token` username
    /// means the password is a bearer token; otherwise exchange the credentials
    /// via the `client_credentials` grant and verify the returned id token.
    pub(super) async fn attempt_basic_auth(&self, username: &str, password: &str) -> Option<Claims> {
        if username == JWT_USERNAME
            && let Some(claims) = self.attempt_bearer_auth(password).await
        {
            return Some(claims);
        }

        let client_id = self.provider.client_id.as_deref()?;
        let scope = self.provider.scopes_to_request.join(" ");
        let id_token = backchannel::client_credentials_token(
            &self.client,
            &self.endpoint.token_url,
            self.token_host.as_deref(),
            client_id,
            username,
            password,
            &scope,
        )
        .await
        .inspect_err(|err| warn!(?err, "client credentials request failed"))
        .ok()
        .flatten()?;

        self.verify_token(&id_token)
            .await
            .inspect_err(|err| warn!(?err, "failed to verify client credentials token"))
            .ok()
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
