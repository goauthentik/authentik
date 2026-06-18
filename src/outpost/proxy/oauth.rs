//! OAuth authorization-code flow helpers.

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

    use axum::http::Uri;
    use url::Url;

    use super::{authorize_url, callback_redirect_uri, redirect_param};

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
}
