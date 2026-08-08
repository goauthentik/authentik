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
    /// The host the issuer was rewritten to, if it was rewritten at all.
    ///
    /// Backchannel token requests have to claim this host *and* scheme, or the
    /// issuer the core mints won't match [`Self::issuer`].
    pub(crate) browser_host: Option<Url>,
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
    /// browser host; backchannel URLs (token, introspection) always keep the
    /// API-provided host. For embedded outposts the browser host is
    /// `authentik_host` and the issuer/JWKS are rewritten to it too (the
    /// backchannel transport overrides the `Host` header). For other outposts,
    /// rewriting only happens when `AUTHENTIK_HOST_BROWSER` is set, and only the
    /// issuer follows the browser host.
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
            browser_host: None,
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
        if embedded {
            ep.jwks_uri = update_url(&ep.jwks_uri, browser_host);
        }
        ep.browser_host = Some(browser_host.clone());

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
        // Nothing was rewritten, so backchannel requests keep their own host.
        assert!(ep.browser_host.is_none());
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
        // The issuer follows `AUTHENTIK_HOST_BROWSER`, so the backchannel host
        // has to as well.
        assert_eq!(ep.browser_host.as_ref(), Some(&browser));
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
        assert_eq!(
            ep.token_url,
            "https://test.goauthentik.io/application/o/token/"
        );
        assert_eq!(
            ep.jwks_uri,
            "https://authentik-host.test.goauthentik.io/application/o/test-app/jwks/"
        );
        assert_eq!(
            ep.end_session_endpoint,
            "https://authentik-host.test.goauthentik.io/application/o/test-app/end-session/"
        );
        assert_eq!(
            ep.token_introspection,
            "https://test.goauthentik.io/application/o/introspect/"
        );
        assert_eq!(ep.browser_host.as_ref(), Some(&authentik_host));
    }

    #[test]
    fn embedded_ignores_browser_host() {
        // Embedded outposts rewrite the issuer to `authentik_host` and ignore
        // `AUTHENTIK_HOST_BROWSER`. The backchannel host must follow the issuer,
        // not `AUTHENTIK_HOST_BROWSER`: a scheme difference between the two makes
        // every minted token fail issuer verification.
        let authentik_host = url("https://authentik-host.test.goauthentik.io");
        let browser = url("http://browser.test.goauthentik.io");
        let ep = OidcEndpoint::new(&oidc(), Some(&authentik_host), Some(&browser), true);

        assert_eq!(
            ep.issuer,
            "https://authentik-host.test.goauthentik.io/application/o/test-app/"
        );
        assert_eq!(ep.browser_host.as_ref(), Some(&authentik_host));
    }
}
