//! Resolving claims from the session, the auth cache, or a bearer token.

use std::{sync::Arc, time::Duration};

use axum::http::{HeaderMap, header::AUTHORIZATION};
use axum_extra::extract::cookie::Cookie;
use base64::{Engine as _, engine::general_purpose::STANDARD as BASE64};
use eyre::{Result, eyre};
use tracing::{Span, field, warn};

use crate::outpost::proxy::{
    application::Application,
    backchannel,
    claims::Claims,
    cookie::SessionCookie,
    oauth,
    session::{SessionData, SessionStore},
    token,
};

/// A resolved request identity, plus an optional session cookie to emit when the
/// identity came from header auth (so cookie-capable clients can reuse the
/// session instead of re-presenting the credential on every request).
pub(super) struct Authenticated {
    pub(super) claims: Claims,
    pub(super) set_cookie: Option<Cookie<'static>>,
}

/// Persist `claims` as a new session and return the cookie carrying its id, or
/// `None` if the session could not be saved.
async fn persist_session(
    store: &SessionStore,
    cookie: &SessionCookie,
    claims: &Claims,
    max_age: Duration,
) -> Option<Cookie<'static>> {
    let sid = oauth::new_session_id();
    let data = SessionData {
        claims: Some(claims.clone()),
        redirect: None,
    };
    if let Err(err) = store.save(&sid, &data, max_age).await {
        warn!(?err, "failed to persist header-auth session");
        return None;
    }
    Some(cookie.build(&sid, max_age))
}

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

/// Decode the username and password from a basic `Authorization` header value.
pub(crate) fn basic_credentials(value: &str) -> Option<(String, String)> {
    const PREFIX: &str = "Basic ";
    if !value.get(..PREFIX.len())?.eq_ignore_ascii_case(PREFIX) {
        return None;
    }
    let decoded = BASE64.decode(value.get(PREFIX.len()..)?).ok()?;
    let decoded = String::from_utf8(decoded).ok()?;
    let (username, password) = decoded.split_once(':')?;
    Some((username.to_owned(), password.to_owned()))
}

/// The label to log for a resolved identity: the preferred username, or the
/// subject when no preferred username is set.
fn user_label(claims: &Claims) -> &str {
    if claims.preferred_username.is_empty() {
        &claims.sub
    } else {
        &claims.preferred_username
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
            &self.api_config.client,
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
            self.verify_rs256_cached(token, &self.endpoint.issuer, client_id)
                .await
        }
    }

    /// Verify an RS256 token against the cached JWKS, refreshing it when the
    /// token's `kid` is not present (e.g. after key rotation).
    async fn verify_rs256_cached(
        &self,
        token: &str,
        issuer: &str,
        audience: &str,
    ) -> Result<Claims> {
        let kid = token::token_kid(token)?.ok_or_else(|| eyre!("token header has no kid"))?;

        if let Some(jwks) = self.jwks_cache.load_full()
            && jwks.find(&kid).is_some()
        {
            return token::verify_rs256(token, &jwks, issuer, audience);
        }

        let jwks =
            backchannel::fetch_jwks(&self.api_config.client, &self.endpoint.jwks_uri).await?;
        let claims = token::verify_rs256(token, &jwks, issuer, audience);
        self.jwks_cache.store(Some(Arc::new(jwks)));
        claims
    }

    /// Resolve claims from HTTP basic auth: a `goauthentik.io/token` username
    /// means the password is a bearer token; otherwise exchange the credentials
    /// via the `client_credentials` grant and verify the returned id token.
    pub(super) async fn attempt_basic_auth(
        &self,
        username: &str,
        password: &str,
    ) -> Option<Claims> {
        if username == JWT_USERNAME
            && let Some(claims) = self.attempt_bearer_auth(password).await
        {
            return Some(claims);
        }

        let client_id = self.provider.client_id.as_deref()?;
        let scope = self.provider.scopes_to_request.join(" ");
        let id_token = backchannel::client_credentials_token(
            &self.api_config.client,
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

    /// Load claims for the request's session, if any.
    async fn claims_from_session(&self, headers: &HeaderMap) -> Option<Claims> {
        let jar = self.session_cookie.jar(headers);
        let sid = self.session_cookie.read(&jar)?;
        self.session_store.load(&sid).await.ok()??.claims
    }

    /// Resolve the request's identity and record the resolved user on the
    /// current request span, reusing the claims we already have instead of
    /// loading the session again.
    pub(super) async fn check_auth(&self, headers: &HeaderMap) -> Option<Authenticated> {
        let authed = self.authenticate(headers).await?;
        Span::current().record("user", field::display(user_label(&authed.claims)));
        Some(authed)
    }

    /// Resolve the request's identity: session, then cached header auth, then a
    /// bearer token, then basic auth. Returns `None` when unauthenticated.
    ///
    /// When the identity is freshly resolved from header auth, a session is
    /// persisted and its cookie returned in [`Authenticated::set_cookie`].
    async fn authenticate(&self, headers: &HeaderMap) -> Option<Authenticated> {
        if let Some(claims) = self.claims_from_session(headers).await {
            return Some(Authenticated {
                claims,
                set_cookie: None,
            });
        }

        let auth_header = Self::authorization_header(headers)?;

        if let Some(claims) = self.cached_claims(auth_header).await {
            return Some(Authenticated {
                claims,
                set_cookie: None,
            });
        }

        // A single `Authorization` header is either bearer or basic, not both.
        let claims = if let Some(token) = bearer_token(auth_header) {
            self.attempt_bearer_auth(token).await
        } else if let Some((username, password)) = basic_credentials(auth_header) {
            self.attempt_basic_auth(&username, &password).await
        } else {
            None
        }?;

        self.cache_claims(auth_header, &claims).await;
        let set_cookie = persist_session(
            &self.session_store,
            &self.session_cookie,
            &claims,
            self.session_max_age(),
        )
        .await;
        Some(Authenticated { claims, set_cookie })
    }
}

#[cfg(test)]
mod tests {
    use std::time::Duration;

    use super::{basic_credentials, bearer_token, persist_session};
    use crate::outpost::proxy::{
        claims::Claims,
        cookie::SessionCookie,
        session::{SessionStore, filesystem::FsSessionStore},
    };

    #[tokio::test]
    async fn persist_session_round_trips() {
        // A header-auth session is persisted and its cookie carries the id that
        // loads it back, so a cookie-capable client can reuse the session.
        let dir = tempfile::tempdir().expect("tempdir");
        let store =
            SessionStore::Filesystem(FsSessionStore::new(dir.path().to_path_buf()).expect("store"));
        let cookie = SessionCookie::new(
            "client-123",
            "0123456789abcdef0123456789abcdef",
            false,
            None,
        )
        .expect("cookie");
        let claims = Claims {
            sub: "user-uuid".to_owned(),
            ..Claims::default()
        };

        let set_cookie = persist_session(&store, &cookie, &claims, Duration::from_mins(1))
            .await
            .expect("session persisted");

        // `build` stores the raw sid as the cookie value.
        let loaded = store
            .load(set_cookie.value())
            .await
            .expect("load")
            .expect("session present");
        assert_eq!(loaded.claims.expect("claims").sub, "user-uuid");
    }

    #[test]
    fn extracts_bearer_token() {
        assert_eq!(bearer_token("Bearer abc123"), Some("abc123"));
        // The scheme is case-insensitive.
        assert_eq!(bearer_token("bearer abc123"), Some("abc123"));
        assert_eq!(bearer_token("Basic abc123"), None);
        assert_eq!(bearer_token("Bearer"), None);
        assert_eq!(bearer_token(""), None);
    }

    #[test]
    fn decodes_basic_credentials() {
        use base64::{Engine as _, engine::general_purpose::STANDARD};

        let header = format!("Basic {}", STANDARD.encode("user:pass"));
        assert_eq!(
            basic_credentials(&header),
            Some(("user".to_owned(), "pass".to_owned()))
        );

        // The password may contain a colon; only the first one separates fields.
        let header = format!("Basic {}", STANDARD.encode("user:pa:ss"));
        assert_eq!(
            basic_credentials(&header),
            Some(("user".to_owned(), "pa:ss".to_owned()))
        );

        assert_eq!(basic_credentials("Bearer something"), None);
        assert_eq!(basic_credentials("Basic not valid base64!!"), None);
    }
}
