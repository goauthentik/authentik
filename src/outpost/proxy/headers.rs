//! Injection of `X-authentik-*` (and derived) headers into upstream requests.

use ak_client::models::ProxyOutpostConfig;
use ak_common::user_agent_outpost;
use axum::http::{HeaderMap, HeaderName, HeaderValue};
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

/// Drop request headers whose name contains an underscore unless a dash-named
/// twin is also present (mitigates underscore/dash header smuggling).
pub(crate) fn remove_underscore_headers(headers: &mut HeaderMap) {
    let stale: Vec<HeaderName> = headers
        .keys()
        .filter(|name| {
            let name = name.as_str();
            name.contains('_') && !headers.contains_key(name.replace('_', "-").as_str())
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

        if let Some(authorization) = basic_auth_header(&self.provider, claims) {
            set_header(headers, "Authorization", &authorization);
        }

        if let Some(proxy) = &claims.ak_proxy
            && let Some(Value::Object(additional)) = proxy.user_attributes.get("additionalHeaders")
        {
            for (name, value) in additional {
                set_header(headers, name, &value_to_string(value));
            }
        }

        remove_underscore_headers(headers);
    }
}

#[cfg(test)]
mod tests {
    use std::collections::HashMap;

    use ak_client::models::ProxyOutpostConfig;
    use axum::http::{HeaderMap, HeaderName, HeaderValue};
    use serde_json::json;

    use super::{basic_auth_header, remove_underscore_headers};
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
    fn underscore_headers_removed_without_dash_twin() {
        let mut headers = HeaderMap::new();
        headers.insert(
            HeaderName::from_static("x_smuggle"),
            HeaderValue::from_static("evil"),
        );
        headers.insert(
            HeaderName::from_static("x_keep"),
            HeaderValue::from_static("a"),
        );
        headers.insert(
            HeaderName::from_static("x-keep"),
            HeaderValue::from_static("b"),
        );
        headers.insert(
            HeaderName::from_static("x-normal"),
            HeaderValue::from_static("c"),
        );

        remove_underscore_headers(&mut headers);

        assert!(!headers.contains_key("x_smuggle"));
        assert!(headers.contains_key("x_keep")); // has a dash twin
        assert!(headers.contains_key("x-keep"));
        assert!(headers.contains_key("x-normal"));
    }
}
