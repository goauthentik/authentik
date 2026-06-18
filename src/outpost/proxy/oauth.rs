//! OAuth authorization-code flow helpers.

use ak_client::models::ProxyMode;
use axum::http::Uri;
use eyre::Result;
use url::{Url, form_urlencoded};
use uuid::Uuid;

pub(crate) const CALLBACK_SIGNATURE: &str = "X-authentik-auth-callback";
pub(crate) const LOGOUT_SIGNATURE: &str = "X-authentik-logout";
pub(crate) const REDIRECT_PARAM: &str = "rd";

/// A fresh random opaque identifier (session id / state nonce).
pub(crate) fn new_session_id() -> String {
    Uuid::new_v4().to_string()
}

/// Extract the `rd` redirect parameter from a request URI, if present.
pub(crate) fn redirect_param(uri: &Uri) -> Option<String> {
    let query = uri.query()?;
    form_urlencoded::parse(query.as_bytes())
        .find(|(key, _)| key.as_ref() == REDIRECT_PARAM)
        .map(|(_, value)| value.into_owned())
}

/// Validate the `rd` redirect parameter against the provider configuration,
/// returning the allowed redirect URL or `None` if it must be rejected.
///
/// For proxy/forward_single the redirect must resolve to the external host (a
/// bare path is resolved against it). For forward_domain the redirect host must
/// end with the cookie domain.
pub(crate) fn check_redirect_param(
    rd: &str,
    mode: ProxyMode,
    external_host: &str,
    cookie_domain: Option<&str>,
) -> Option<String> {
    if rd.is_empty() {
        return None;
    }
    match mode {
        ProxyMode::Proxy | ProxyMode::ForwardSingle => {
            let ext = Url::parse(external_host).ok()?;
            let resolved = ext.join(rd).ok()?;
            if resolved.host_str() != ext.host_str() || resolved.port() != ext.port() {
                return None;
            }
            Some(resolved.into())
        }
        ProxyMode::ForwardDomain => {
            let domain = cookie_domain?.trim_start_matches('.');
            let resolved = Url::parse(rd).ok()?;
            if !resolved.host_str()?.ends_with(domain) {
                return None;
            }
            Some(resolved.into())
        }
    }
}

/// Join `path` onto `base`, returning `base` unchanged if it cannot be parsed.
pub(crate) fn url_join(base: &str, path: &str) -> String {
    Url::parse(base)
        .and_then(|url| url.join(path))
        .map_or_else(|_| base.to_owned(), Into::into)
}

/// `{external_host}/outpost.goauthentik.io/start?rd={redirect}`.
pub(crate) fn start_url(external_host: &str, redirect: &str) -> Result<String> {
    let mut url = Url::parse(external_host)?;
    url.set_path("/outpost.goauthentik.io/start");
    url.query_pairs_mut().append_pair(REDIRECT_PARAM, redirect);
    Ok(url.into())
}

/// `{external_host}/outpost.goauthentik.io/callback?X-authentik-auth-callback=true`.
pub(crate) fn callback_redirect_uri(external_host: &str) -> Result<String> {
    let mut url = Url::parse(external_host)?;
    url.set_path("/outpost.goauthentik.io/callback");
    url.query_pairs_mut().append_pair(CALLBACK_SIGNATURE, "true");
    Ok(url.into())
}

/// Build the authorization URL for the authorization-code flow.
pub(crate) fn authorize_url(
    auth_url: &str,
    client_id: &str,
    redirect_uri: &str,
    scopes: &[String],
    state: &str,
) -> Result<String> {
    let mut url = Url::parse(auth_url)?;
    url.query_pairs_mut()
        .append_pair("client_id", client_id)
        .append_pair("redirect_uri", redirect_uri)
        .append_pair("response_type", "code")
        .append_pair("scope", &scopes.join(" "))
        .append_pair("state", state);
    Ok(url.into())
}

#[cfg(test)]
mod tests {
    use std::collections::HashMap;

    use ak_client::models::ProxyMode;
    use axum::http::Uri;
    use url::Url;

    use super::{authorize_url, callback_redirect_uri, check_redirect_param, redirect_param, start_url};

    #[test]
    fn builds_callback_redirect_uri() {
        assert_eq!(
            callback_redirect_uri("https://app.example.com").expect("redirect uri"),
            "https://app.example.com/outpost.goauthentik.io/callback?X-authentik-auth-callback=true"
        );
    }

    #[test]
    fn builds_authorize_url() {
        let scopes = vec!["openid".to_owned(), "profile".to_owned()];
        let url = authorize_url(
            "https://authentik.example.com/application/o/authorize/",
            "client-123",
            "https://app.example.com/outpost.goauthentik.io/callback?X-authentik-auth-callback=true",
            &scopes,
            "state-token",
        )
        .expect("authorize url");

        let parsed = Url::parse(&url).expect("valid url");
        let params: HashMap<_, _> = parsed.query_pairs().into_owned().collect();

        assert_eq!(parsed.path(), "/application/o/authorize/");
        assert_eq!(params["client_id"], "client-123");
        assert_eq!(params["response_type"], "code");
        assert_eq!(params["scope"], "openid profile");
        assert_eq!(params["state"], "state-token");
        assert_eq!(
            params["redirect_uri"],
            "https://app.example.com/outpost.goauthentik.io/callback?X-authentik-auth-callback=true"
        );
    }

    #[test]
    fn extracts_redirect_param() {
        let uri: Uri = "/outpost.goauthentik.io/start?rd=https%3A%2F%2Fapp.example.com%2Fpage"
            .parse()
            .expect("valid uri");
        assert_eq!(
            redirect_param(&uri),
            Some("https://app.example.com/page".to_owned())
        );
    }

    #[test]
    fn missing_redirect_param_is_none() {
        let uri: Uri = "/outpost.goauthentik.io/start".parse().expect("valid uri");
        assert_eq!(redirect_param(&uri), None);
    }

    #[test]
    fn check_redirect_proxy_same_host() {
        assert_eq!(
            check_redirect_param(
                "https://app.example.com/page",
                ProxyMode::Proxy,
                "https://app.example.com",
                None,
            ),
            Some("https://app.example.com/page".to_owned())
        );
    }

    #[test]
    fn check_redirect_proxy_path_only() {
        assert_eq!(
            check_redirect_param("/page", ProxyMode::Proxy, "https://app.example.com", None),
            Some("https://app.example.com/page".to_owned())
        );
    }

    #[test]
    fn check_redirect_proxy_rejects_other_host() {
        assert_eq!(
            check_redirect_param(
                "https://evil.example.com/page",
                ProxyMode::Proxy,
                "https://app.example.com",
                None,
            ),
            None
        );
    }

    #[test]
    fn check_redirect_forward_domain_suffix() {
        assert_eq!(
            check_redirect_param(
                "https://sub.example.com/page",
                ProxyMode::ForwardDomain,
                "https://auth.example.com",
                Some(".example.com"),
            ),
            Some("https://sub.example.com/page".to_owned())
        );
        assert_eq!(
            check_redirect_param(
                "https://evil.com/page",
                ProxyMode::ForwardDomain,
                "https://auth.example.com",
                Some(".example.com"),
            ),
            None
        );
    }

    #[test]
    fn builds_start_url() {
        assert_eq!(
            start_url("https://app.example.com", "https://app.example.com/page").expect("start url"),
            "https://app.example.com/outpost.goauthentik.io/start?rd=https%3A%2F%2Fapp.example.com%2Fpage"
        );
    }
}
