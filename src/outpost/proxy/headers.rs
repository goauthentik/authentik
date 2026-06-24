//! Injection of `X-authentik-*` (and derived) headers into upstream requests.

use std::collections::HashSet;

use ak_client::models::ProxyOutpostConfig;
use ak_common::user_agent_outpost;
use axum::http::{HeaderMap, HeaderName, HeaderValue, header::AUTHORIZATION};
use base64::{Engine as _, engine::general_purpose::STANDARD as BASE64};
use serde_json::Value;

use crate::outpost::proxy::{application::Application, claims::Claims};

/// Set a header, overwriting any existing value. Invalid names/values are skipped.
fn set_header(headers: &mut HeaderMap, name: &str, value: &str) {
    if let (Ok(name), Ok(value)) = (
        HeaderName::from_bytes(name.as_bytes()),
        HeaderValue::from_str(value),
    ) {
        headers.insert(name, value);
    }
}

/// Render a JSON attribute value as a header string.
fn value_to_string(value: &Value) -> String {
    match value {
        Value::String(string) => string.clone(),
        Value::Null => String::new(),
        other => other.to_string(),
    }
}

/// Build the basic-auth `Authorization` value from the user's attributes, if enabled.
pub(crate) fn basic_auth_header(provider: &ProxyOutpostConfig, claims: &Claims) -> Option<String> {
    if provider.basic_auth_enabled != Some(true) {
        return None;
    }
    let attributes = &claims.ak_proxy.as_ref()?.user_attributes;
    let attribute = |key: &Option<String>| -> Option<&str> {
        key.as_deref()
            .and_then(|key| attributes.get(key))
            .and_then(Value::as_str)
    };

    let password = attribute(&provider.basic_auth_password_attribute).unwrap_or_default();
    if password.is_empty() {
        return None;
    }
    let username = attribute(&provider.basic_auth_user_attribute).unwrap_or(&claims.email);

    let encoded = BASE64.encode(format!("{username}:{password}"));
    Some(format!("Basic {encoded}"))
}

/// Set the `Authorization` header sent upstream.
///
/// The client's own inbound `Authorization` (e.g. the bearer token the proxy
/// just consumed to authenticate the request) is never forwarded upstream. If
/// basic-auth-to-upstream is configured, its value is set in its place.
fn set_upstream_authorization(
    headers: &mut HeaderMap,
    provider: &ProxyOutpostConfig,
    claims: &Claims,
) {
    headers.remove(AUTHORIZATION);
    if let Some(authorization) = basic_auth_header(provider, claims) {
        set_header(headers, "Authorization", &authorization);
    }
}

/// Drop an inbound header containing `_` when its dash-equivalent is *also*
/// present — e.g. remove `X_authentik_username` when the real
/// `X-authentik-username` exists, or `X_Request_Id` when `X-Request-Id` does.
///
/// This stops a client from shadowing a trusted dash header on upstreams that
/// treat `_` and `-` alike, while leaving standalone underscore headers
/// (legitimate application headers with no dash twin) untouched. Because the
/// `X-authentik-*` headers are always set just before this runs, their underscore
/// spoofs always have a twin and are always removed.
pub(crate) fn remove_shadowed_underscore_headers(headers: &mut HeaderMap) {
    // Snapshot the present names so we can test for a dash twin without holding a
    // borrow on `headers` while removing from it. `HeaderName` is lowercase.
    let present: HashSet<String> = headers
        .keys()
        .map(|name| name.as_str().to_owned())
        .collect();
    let stale: Vec<HeaderName> = headers
        .keys()
        .filter(|name| {
            let name = name.as_str();
            name.contains('_') && present.contains(&name.replace('_', "-"))
        })
        .cloned()
        .collect();
    for name in stale {
        headers.remove(&name);
    }
}

impl Application {
    /// Inject the authenticated user's headers into an upstream request.
    pub(super) fn add_upstream_headers(&self, headers: &mut HeaderMap, claims: &Claims) {
        let injected = [
            ("X-authentik-username", claims.preferred_username.clone()),
            ("X-authentik-groups", claims.groups.join("|")),
            ("X-authentik-entitlements", claims.entitlements.join("|")),
            ("X-authentik-email", claims.email.clone()),
            ("X-authentik-name", claims.name.clone()),
            ("X-authentik-uid", claims.sub.clone()),
            ("X-authentik-jwt", claims.raw_token.clone()),
            ("X-authentik-meta-jwks", self.endpoint.jwks_uri.clone()),
            ("X-authentik-meta-outpost", self.outpost_name.clone()),
            ("X-authentik-meta-provider", self.provider.name.clone()),
            (
                "X-authentik-meta-app",
                self.provider.assigned_application_slug.clone(),
            ),
            ("X-authentik-meta-version", user_agent_outpost()),
        ];
        for (name, value) in injected {
            set_header(headers, name, &value);
        }

        set_upstream_authorization(headers, &self.provider, claims);

        if let Some(proxy) = &claims.ak_proxy
            && let Some(Value::Object(additional)) = proxy.user_attributes.get("additionalHeaders")
        {
            for (name, value) in additional {
                set_header(headers, name, &value_to_string(value));
            }
        }

        remove_shadowed_underscore_headers(headers);
    }
}

#[cfg(test)]
mod tests {
    use std::collections::HashMap;

    use ak_client::models::ProxyOutpostConfig;
    use axum::http::{HeaderMap, HeaderName, HeaderValue, header::AUTHORIZATION};
    use serde_json::json;

    use super::{
        basic_auth_header, remove_shadowed_underscore_headers, set_upstream_authorization,
    };
    use crate::outpost::proxy::claims::{Claims, ProxyClaims};

    fn provider() -> ProxyOutpostConfig {
        ProxyOutpostConfig {
            basic_auth_enabled: Some(true),
            basic_auth_user_attribute: Some("ldap_username".to_owned()),
            basic_auth_password_attribute: Some("ldap_password".to_owned()),
            ..Default::default()
        }
    }

    #[test]
    fn basic_auth_from_attributes() {
        let claims = Claims {
            email: "fallback@example.com".to_owned(),
            ak_proxy: Some(ProxyClaims {
                user_attributes: HashMap::from([
                    ("ldap_username".to_owned(), json!("svc")),
                    ("ldap_password".to_owned(), json!("secret")),
                ]),
                ..Default::default()
            }),
            ..Default::default()
        };

        // base64("svc:secret")
        assert_eq!(
            basic_auth_header(&provider(), &claims),
            Some("Basic c3ZjOnNlY3JldA==".to_owned())
        );
    }

    #[test]
    fn basic_auth_falls_back_to_email_username() {
        let claims = Claims {
            email: "user@example.com".to_owned(),
            ak_proxy: Some(ProxyClaims {
                user_attributes: HashMap::from([("ldap_password".to_owned(), json!("secret"))]),
                ..Default::default()
            }),
            ..Default::default()
        };

        // base64("user@example.com:secret")
        assert_eq!(
            basic_auth_header(&provider(), &claims),
            Some("Basic dXNlckBleGFtcGxlLmNvbTpzZWNyZXQ=".to_owned())
        );
    }

    #[test]
    fn basic_auth_disabled_or_empty_password() {
        let claims = Claims {
            ak_proxy: Some(ProxyClaims {
                user_attributes: HashMap::from([("ldap_password".to_owned(), json!("secret"))]),
                ..Default::default()
            }),
            ..Default::default()
        };
        let mut disabled = provider();
        disabled.basic_auth_enabled = Some(false);
        assert_eq!(basic_auth_header(&disabled, &claims), None);

        // No password attribute present -> no header.
        let no_password = Claims {
            ak_proxy: Some(ProxyClaims::default()),
            ..Default::default()
        };
        assert_eq!(basic_auth_header(&provider(), &no_password), None);
    }

    #[test]
    fn inbound_authorization_is_dropped() {
        // The client's inbound Authorization must not leak upstream when
        // basic-auth-to-upstream is not configured.
        let mut provider = provider();
        provider.basic_auth_enabled = Some(false);

        let mut headers = HeaderMap::new();
        headers.insert(
            AUTHORIZATION,
            HeaderValue::from_static("Bearer client-token"),
        );

        set_upstream_authorization(&mut headers, &provider, &Claims::default());

        assert!(!headers.contains_key(AUTHORIZATION));
    }

    #[test]
    fn basic_auth_replaces_inbound_authorization() {
        // With basic-auth-to-upstream enabled, the inbound Authorization is
        // replaced by the derived basic-auth value rather than forwarded.
        let claims = Claims {
            email: "user@example.com".to_owned(),
            ak_proxy: Some(ProxyClaims {
                user_attributes: HashMap::from([
                    ("ldap_username".to_owned(), json!("svc")),
                    ("ldap_password".to_owned(), json!("secret")),
                ]),
                ..Default::default()
            }),
            ..Default::default()
        };

        let mut headers = HeaderMap::new();
        headers.insert(
            AUTHORIZATION,
            HeaderValue::from_static("Bearer client-token"),
        );

        set_upstream_authorization(&mut headers, &provider(), &claims);

        assert_eq!(
            headers
                .get(AUTHORIZATION)
                .and_then(|value| value.to_str().ok()),
            Some("Basic c3ZjOnNlY3JldA==")
        );
    }

    #[test]
    fn shadowed_underscore_headers_are_removed() {
        let mut headers = HeaderMap::new();
        // Underscore (and mixed) spoofs of an authentik header — the real dash
        // header is present (we always set it), so they are removed.
        headers.insert(
            HeaderName::from_static("x_authentik_username"),
            HeaderValue::from_static("attacker"),
        );
        headers.insert(
            HeaderName::from_static("x-authentik_username"),
            HeaderValue::from_static("attacker"),
        );
        headers.insert(
            HeaderName::from_static("x-authentik-username"),
            HeaderValue::from_static("real"),
        );
        // An underscore header that duplicates a present dash header is dropped...
        headers.insert(
            HeaderName::from_static("x_request_id"),
            HeaderValue::from_static("spoof"),
        );
        headers.insert(
            HeaderName::from_static("x-request-id"),
            HeaderValue::from_static("real-id"),
        );
        // ...but a standalone underscore header with no dash twin is preserved.
        headers.insert(
            HeaderName::from_static("x_trace_token"),
            HeaderValue::from_static("keep-me"),
        );
        headers.insert(
            HeaderName::from_static("x-normal"),
            HeaderValue::from_static("c"),
        );

        remove_shadowed_underscore_headers(&mut headers);

        assert!(!headers.contains_key("x_authentik_username"));
        assert!(!headers.contains_key("x-authentik_username"));
        assert!(headers.contains_key("x-authentik-username"));
        assert!(!headers.contains_key("x_request_id"));
        assert!(headers.contains_key("x-request-id"));
        assert!(headers.contains_key("x_trace_token"));
        assert!(headers.contains_key("x-normal"));
    }
}
