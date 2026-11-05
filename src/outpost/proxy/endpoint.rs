//! Resolved OIDC endpoints for a provider, with browser/backchannel host rewriting.

use ak_client::models::OpenIdConnectConfiguration;
use url::Url;

/// OIDC endpoints used by the proxy, after host rewriting.
#[derive(Debug, Clone)]
pub(crate) struct OidcEndpoint {
    pub(crate) auth_url: String,
    pub(crate) token_url: String,
    pub(crate) token_introspection: String,
    pub(crate) end_session_endpoint: String,
    pub(crate) jwks_uri: String,
    pub(crate) issuer: String,
}

/// Rewrite the scheme and host (and port) of `raw` to match `base`, leaving the
/// path/query/fragment untouched. Returns `raw` unchanged if it cannot be parsed.
fn update_url(raw: &str, base: &Url) -> String {
    let Ok(mut url) = Url::parse(raw) else {
        return raw.to_owned();
    };
    let _ = url.set_scheme(base.scheme());
    let _ = url.set_host(base.host_str());
    let _ = url.set_port(base.port());
    url.to_string()
}

impl OidcEndpoint {
    /// Build the endpoints from the provider OIDC configuration.
    ///
    /// Browser-facing URLs (authorize, end-session) are rewritten to the
    /// browser host, as is the issuer, so the tokens the browser sees carry the
    /// public host. Backchannel URLs (token, introspection and JWKS) always keep
    /// the API-provided host: the embedded outpost reaches the core over a unix
    /// socket with plain HTTP, so rewriting one of them to the `https://` browser
    /// host would make that socket client attempt a TLS handshake on a plain
    /// socket and fail. For embedded outposts the browser host is
    /// `authentik_host`; for other outposts, rewriting only happens when
    /// `AUTHENTIK_HOST_BROWSER` is set, and only the issuer follows the browser
    /// host.
    pub(crate) fn new(
        oidc: &OpenIdConnectConfiguration,
        authentik_host: Option<&Url>,
        host_browser: Option<&Url>,
        embedded: bool,
    ) -> Self {
        let mut ep = Self {
            auth_url: oidc.authorization_endpoint.clone(),
            token_url: oidc.token_endpoint.clone(),
            token_introspection: oidc.introspection_endpoint.clone(),
            end_session_endpoint: oidc.end_session_endpoint.clone(),
            jwks_uri: oidc.jwks_uri.clone(),
            issuer: oidc.issuer.clone(),
        };

        let browser_host = if embedded {
            match authentik_host {
                Some(host) => host,
                None => return ep,
            }
        } else {
            match host_browser {
                Some(host) => host,
                None => return ep,
            }
        };

        ep.auth_url = update_url(&ep.auth_url, browser_host);
        ep.end_session_endpoint = update_url(&ep.end_session_endpoint, browser_host);
        ep.issuer = update_url(&ep.issuer, browser_host);

        ep
    }
}

#[cfg(test)]
mod tests {
    use ak_client::models::OpenIdConnectConfiguration;
    use url::Url;

    use super::OidcEndpoint;

    fn oidc() -> OpenIdConnectConfiguration {
        OpenIdConnectConfiguration {
            authorization_endpoint: "https://test.goauthentik.io/application/o/authorize/"
                .to_owned(),
            end_session_endpoint: "https://test.goauthentik.io/application/o/test-app/end-session/"
                .to_owned(),
            introspection_endpoint: "https://test.goauthentik.io/application/o/introspect/"
                .to_owned(),
            issuer: "https://test.goauthentik.io/application/o/test-app/".to_owned(),
            jwks_uri: "https://test.goauthentik.io/application/o/test-app/jwks/".to_owned(),
            token_endpoint: "https://test.goauthentik.io/application/o/token/".to_owned(),
            ..Default::default()
        }
    }

    fn url(raw: &str) -> Url {
        Url::parse(raw).expect("valid url")
    }

    #[test]
    fn default_non_embedded() {
        let authentik_host = url("https://authentik-host.test.goauthentik.io");
        let ep = OidcEndpoint::new(&oidc(), Some(&authentik_host), None, false);

        assert_eq!(
            ep.auth_url,
            "https://test.goauthentik.io/application/o/authorize/"
        );
        assert_eq!(
            ep.token_url,
            "https://test.goauthentik.io/application/o/token/"
        );
        assert_eq!(
            ep.issuer,
            "https://test.goauthentik.io/application/o/test-app/"
        );
        assert_eq!(
            ep.jwks_uri,
            "https://test.goauthentik.io/application/o/test-app/jwks/"
        );
        assert_eq!(
            ep.end_session_endpoint,
            "https://test.goauthentik.io/application/o/test-app/end-session/"
        );
        assert_eq!(
            ep.token_introspection,
            "https://test.goauthentik.io/application/o/introspect/"
        );
    }

    #[test]
    fn non_embedded_with_browser_host() {
        let authentik_host = url("https://authentik-host.test.goauthentik.io");
        let browser = url("https://browser.test.goauthentik.io");
        let ep = OidcEndpoint::new(&oidc(), Some(&authentik_host), Some(&browser), false);

        assert_eq!(
            ep.auth_url,
            "https://browser.test.goauthentik.io/application/o/authorize/"
        );
        assert_eq!(
            ep.end_session_endpoint,
            "https://browser.test.goauthentik.io/application/o/test-app/end-session/"
        );
        assert_eq!(
            ep.token_url,
            "https://test.goauthentik.io/application/o/token/"
        );
        assert_eq!(
            ep.issuer,
            "https://browser.test.goauthentik.io/application/o/test-app/"
        );
        assert_eq!(
            ep.jwks_uri,
            "https://test.goauthentik.io/application/o/test-app/jwks/"
        );
        assert_eq!(
            ep.token_introspection,
            "https://test.goauthentik.io/application/o/introspect/"
        );
    }

    #[test]
    fn embedded() {
        let authentik_host = url("https://authentik-host.test.goauthentik.io");
        let ep = OidcEndpoint::new(&oidc(), Some(&authentik_host), None, true);

        assert_eq!(
            ep.auth_url,
            "https://authentik-host.test.goauthentik.io/application/o/authorize/"
        );
        assert_eq!(
            ep.issuer,
            "https://authentik-host.test.goauthentik.io/application/o/test-app/"
        );
        // Token, introspection and JWKS are backchannel URLs and keep the API-provided host:
        // the embedded outpost fetches them over the unix socket as plain HTTP, so rewriting
        // the JWKS URL to the `https://` browser host would make that socket client attempt TLS.
        assert_eq!(
            ep.token_url,
            "https://test.goauthentik.io/application/o/token/"
        );
        assert_eq!(
            ep.jwks_uri,
            "https://test.goauthentik.io/application/o/test-app/jwks/"
        );
        assert_eq!(
            ep.end_session_endpoint,
            "https://authentik-host.test.goauthentik.io/application/o/test-app/end-session/"
        );
        assert_eq!(
            ep.token_introspection,
            "https://test.goauthentik.io/application/o/introspect/"
        );
    }
}
