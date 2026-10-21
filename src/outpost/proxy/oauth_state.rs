//! OAuth `state` parameter, encoded as an HS256 JWT signed with the provider's
//! cookie secret.
//!
//! The token carries no `exp`/`aud`; only the issuer is validated on decode.

use std::collections::HashSet;

use jsonwebtoken::{Algorithm, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};

/// Build the issuer string for a provider's OAuth state token.
pub(crate) fn issuer(client_id: &str) -> String {
    format!("goauthentik.io/outpost/{client_id}")
}

/// The contents of the OAuth `state` parameter.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub(crate) struct OAuthState {
    pub(crate) iss: String,
    pub(crate) sid: String,
    pub(crate) state: String,
    pub(crate) redirect: String,
}

impl OAuthState {
    /// Sign the state into a compact HS256 JWT using the provider cookie secret.
    pub(crate) fn encode(&self, cookie_secret: &str) -> jsonwebtoken::errors::Result<String> {
        jsonwebtoken::encode(
            &Header::new(Algorithm::HS256),
            self,
            &EncodingKey::from_secret(cookie_secret.as_bytes()),
        )
    }

    /// Verify and decode a state JWT, enforcing the HS256 signature and the
    /// expected issuer. Expiry and audience are intentionally not validated, as
    /// the token carries neither.
    pub(crate) fn decode(
        token: &str,
        cookie_secret: &str,
        expected_issuer: &str,
    ) -> jsonwebtoken::errors::Result<Self> {
        let mut validation = Validation::new(Algorithm::HS256);
        // The state token carries no registered claims, so don't require `exp`.
        validation.required_spec_claims = HashSet::new();
        validation.validate_exp = false;
        validation.validate_aud = false;
        validation.set_issuer(&[expected_issuer]);

        let data = jsonwebtoken::decode::<Self>(
            token,
            &DecodingKey::from_secret(cookie_secret.as_bytes()),
            &validation,
        )?;
        Ok(data.claims)
    }
}

#[cfg(test)]
mod tests {
    use super::{OAuthState, issuer};

    fn sample(client_id: &str) -> OAuthState {
        OAuthState {
            iss: issuer(client_id),
            sid: "session-id".to_owned(),
            state: "random-nonce".to_owned(),
            redirect: "https://app.example.com/dashboard".to_owned(),
        }
    }

    #[test]
    fn round_trip() {
        let secret = "cookie-secret";
        let client_id = "client-123";
        let state = sample(client_id);

        let token = state.encode(secret).expect("failed to encode state");
        let decoded =
            OAuthState::decode(&token, secret, &issuer(client_id)).expect("failed to decode state");

        assert_eq!(state, decoded);
    }

    #[test]
    fn rejects_issuer_mismatch() {
        let secret = "cookie-secret";
        let state = sample("client-123");

        let token = state.encode(secret).expect("failed to encode state");

        OAuthState::decode(&token, secret, &issuer("other-client"))
            .expect_err("decode should reject a mismatched issuer");
    }

    #[test]
    fn rejects_wrong_secret() {
        let client_id = "client-123";
        let state = sample(client_id);

        let token = state
            .encode("cookie-secret")
            .expect("failed to encode state");

        OAuthState::decode(&token, "wrong-secret", &issuer(client_id))
            .expect_err("decode should reject a bad signature");
    }
}
