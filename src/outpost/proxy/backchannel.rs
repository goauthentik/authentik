//! Backchannel (server-to-server) OAuth calls.

use eyre::Result;
use jsonwebtoken::jwk::JwkSet;
use reqwest::header::{HOST, HeaderName};
use reqwest_middleware::{ClientWithMiddleware, RequestBuilder};
use serde::Deserialize;
use url::Url;

use crate::outpost::proxy::claims::Claims;

const X_FORWARDED_PROTO: HeaderName = HeaderName::from_static("x-forwarded-proto");

/// The host and scheme to claim on backchannel requests.
///
/// The core derives a provider's issuer from the request host and forwarded
/// scheme, so a request sent to the internal host has to present the
/// browser-facing one for the resulting token to verify against
/// [`OidcEndpoint::issuer`](crate::outpost::proxy::endpoint::OidcEndpoint).
#[derive(Debug, Clone)]
pub(crate) struct TokenHost {
    host: String,
    scheme: String,
}

impl TokenHost {
    /// Build the override from a browser-facing URL, or `None` if it has no host.
    pub(crate) fn new(url: &Url) -> Option<Self> {
        let host = url.host_str()?;
        Some(Self {
            host: match url.port() {
                Some(port) => format!("{host}:{port}"),
                None => host.to_owned(),
            },
            scheme: url.scheme().to_owned(),
        })
    }

    fn apply(&self, request: RequestBuilder) -> RequestBuilder {
        request
            .header(HOST, self.host.as_str())
            .header(X_FORWARDED_PROTO, self.scheme.as_str())
    }
}

#[derive(Deserialize)]
struct TokenResponse {
    #[serde(default)]
    access_token: String,
    #[serde(default)]
    id_token: String,
}

#[derive(Deserialize)]
struct IntrospectionResponse {
    #[serde(flatten)]
    claims: Claims,
    #[serde(default)]
    active: bool,
}

/// Exchange an authorization code for an access token (used as the ID token).
///
/// `token_host`, when set, makes the request claim the browser-facing host and
/// scheme so the issuer matches even though the request goes over the
/// backchannel.
pub(crate) async fn exchange_code(
    client: &ClientWithMiddleware,
    token_url: &str,
    token_host: Option<&TokenHost>,
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
        request = host.apply(request);
    }
    let response = request.send().await?.error_for_status()?;
    Ok(response.json::<TokenResponse>().await?.access_token)
}

/// Fetch and parse the provider JWKS.
pub(crate) async fn fetch_jwks(client: &ClientWithMiddleware, jwks_uri: &str) -> Result<JwkSet> {
    let response = client.get(jwks_uri).send().await?.error_for_status()?;
    Ok(response.json::<JwkSet>().await?)
}

/// Request a token via the `client_credentials` grant, returning the id token.
pub(crate) async fn client_credentials_token(
    client: &ClientWithMiddleware,
    token_url: &str,
    token_host: Option<&TokenHost>,
    client_id: &str,
    username: &str,
    password: &str,
    scope: &str,
) -> Result<Option<String>> {
    let mut request = client.post(token_url).form(&[
        ("grant_type", "client_credentials"),
        ("client_id", client_id),
        ("username", username),
        ("password", password),
        ("scope", scope),
    ]);
    if let Some(host) = token_host {
        request = host.apply(request);
    }
    let response = request.send().await?;
    if !response.status().is_success() {
        return Ok(None);
    }
    Ok(Some(response.json::<TokenResponse>().await?.id_token))
}

/// Introspect a bearer token, returning its claims when the token is active.
pub(crate) async fn introspect_token(
    client: &ClientWithMiddleware,
    introspection_url: &str,
    token_host: Option<&TokenHost>,
    client_id: &str,
    client_secret: &str,
    token: &str,
) -> Result<Option<Claims>> {
    let mut request = client.post(introspection_url).form(&[
        ("client_id", client_id),
        ("client_secret", client_secret),
        ("token", token),
    ]);
    if let Some(host) = token_host {
        request = host.apply(request);
    }
    let response = request.send().await?;
    if !response.status().is_success() {
        return Ok(None);
    }
    let introspection = response.json::<IntrospectionResponse>().await?;
    if !introspection.active {
        return Ok(None);
    }
    let mut claims = introspection.claims;
    token.clone_into(&mut claims.raw_token);
    Ok(Some(claims))
}

#[cfg(test)]
mod tests {
    use reqwest::header::HOST;
    use reqwest_middleware::{ClientBuilder, ClientWithMiddleware};
    use url::Url;

    use super::{TokenHost, X_FORWARDED_PROTO};

    fn client() -> ClientWithMiddleware {
        ClientBuilder::new(reqwest::Client::new()).build()
    }

    fn token_host(raw: &str) -> TokenHost {
        TokenHost::new(&Url::parse(raw).expect("valid url")).expect("url has a host")
    }

    #[test]
    fn overrides_host_and_forwarded_scheme() {
        // A request to the internal token endpoint must claim the browser-facing host and scheme,
        // otherwise the core mints a token whose issuer is `http://...` and verification against
        // the `https://` issuer fails.
        let request = token_host("https://authentik.test.goauthentik.io/")
            .apply(client().post("http://localhost:8000/application/o/token/"))
            .build()
            .expect("failed to build request");

        assert_eq!(
            request.headers().get(HOST).expect("host header"),
            "authentik.test.goauthentik.io"
        );
        assert_eq!(
            request
                .headers()
                .get(X_FORWARDED_PROTO)
                .expect("forwarded proto header"),
            "https"
        );
    }

    #[test]
    fn keeps_non_default_port() {
        let host = token_host("http://authentik.test.goauthentik.io:9000/");
        assert_eq!(host.host, "authentik.test.goauthentik.io:9000");
        assert_eq!(host.scheme, "http");

        assert_eq!(
            token_host("https://authentik.test.goauthentik.io:443/").host,
            "authentik.test.goauthentik.io"
        );
    }

    #[test]
    fn rejects_url_without_host() {
        assert!(TokenHost::new(&Url::parse("file:///tmp/authentik").expect("valid url")).is_none());
    }
}
