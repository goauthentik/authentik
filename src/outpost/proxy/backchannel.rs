//! Backchannel (server-to-server) OAuth calls.

use eyre::Result;
use jsonwebtoken::jwk::JwkSet;
use reqwest::header::HOST;
use reqwest_middleware::ClientWithMiddleware;
use serde::Deserialize;

#[derive(Deserialize)]
struct TokenResponse {
    access_token: String,
}

/// Exchange an authorization code for an access token (used as the ID token).
///
/// `token_host`, when set, overrides the `Host` header so the issuer matches the
/// browser-facing host even though the request is sent over the backchannel.
pub(crate) async fn exchange_code(
    client: &ClientWithMiddleware,
    token_url: &str,
    token_host: Option<&str>,
    code: &str,
    redirect_uri: &str,
    client_id: &str,
    client_secret: &str,
) -> Result<String> {
    let mut request = client.post(token_url).form(&[
        ("grant_type", "authorization_code"),
        ("code", code),
        ("redirect_uri", redirect_uri),
        ("client_id", client_id),
        ("client_secret", client_secret),
    ]);
    if let Some(host) = token_host {
        request = request.header(HOST, host);
    }
    let response = request.send().await?.error_for_status()?;
    Ok(response.json::<TokenResponse>().await?.access_token)
}

/// Fetch and parse the provider JWKS.
pub(crate) async fn fetch_jwks(client: &ClientWithMiddleware, jwks_uri: &str) -> Result<JwkSet> {
    let response = client.get(jwks_uri).send().await?.error_for_status()?;
    Ok(response.json::<JwkSet>().await?)
}
