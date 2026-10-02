//! Claims carried in the OIDC ID token and persisted in the session.

use std::collections::HashMap;

use serde::{Deserialize, Serialize};

/// Proxy-specific claims.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub(crate) struct ProxyClaims {
    pub(crate) user_attributes: HashMap<String, serde_json::Value>,
    pub(crate) backend_override: String,
    pub(crate) host_header: String,
    pub(crate) is_superuser: bool,
}

/// Claims extracted from a verified ID token.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub(crate) struct Claims {
    pub(crate) sub: String,
    pub(crate) exp: i64,
    pub(crate) email: String,
    pub(crate) email_verified: bool,
    pub(crate) name: String,
    pub(crate) preferred_username: String,
    pub(crate) groups: Vec<String>,
    pub(crate) entitlements: Vec<String>,
    pub(crate) sid: String,
    pub(crate) ak_proxy: Option<ProxyClaims>,
    pub(crate) raw_token: String,
}

#[cfg(test)]
mod tests {
    use std::collections::HashMap;

    use serde_json::json;

    use super::{Claims, ProxyClaims};

    #[test]
    fn round_trip() {
        let claims = Claims {
            sub: "user-uuid".to_owned(),
            exp: 1_700_000_000_i64,
            email: "user@example.com".to_owned(),
            email_verified: true,
            name: "Example User".to_owned(),
            preferred_username: "akadmin".to_owned(),
            groups: vec!["authentik Admins".to_owned(), "users".to_owned()],
            entitlements: vec!["can_do_thing".to_owned()],
            sid: "session-id".to_owned(),
            ak_proxy: Some(ProxyClaims {
                user_attributes: HashMap::from([(
                    "additionalHeaders".to_owned(),
                    json!({"X-Foo": "bar"}),
                )]),
                backend_override: "http://backend:8080".to_owned(),
                host_header: "internal.example.com".to_owned(),
                is_superuser: true,
            }),
            raw_token: "the.raw.jwt".to_owned(),
        };

        let serialized = serde_json::to_string(&claims).expect("failed to serialize claims");
        let deserialized: Claims =
            serde_json::from_str(&serialized).expect("failed to deserialize claims");

        assert_eq!(claims, deserialized);
    }

    #[test]
    fn missing_fields_default() {
        // A minimal ID token may omit most claims; they should default rather
        // than fail to deserialize
        let claims: Claims = serde_json::from_value(json!({
            "sub": "user-uuid",
        }))
        .expect("failed to deserialize minimal claims");

        assert_eq!(claims.sub, "user-uuid");
        assert!(claims.groups.is_empty());
        assert!(claims.entitlements.is_empty());
        assert!(claims.ak_proxy.is_none());
        assert_eq!(claims.exp, 0_i64);
    }
}
