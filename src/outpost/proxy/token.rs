//! Verification of authentik-issued access tokens (used as ID tokens).

use eyre::{Result, eyre};
use jsonwebtoken::{Algorithm, DecodingKey, Validation, decode, decode_header, jwk::JwkSet};

use crate::outpost::proxy::claims::{Claims, ProxyClaims};

fn validation(alg: Algorithm, issuer: &str, audience: &str) -> Validation {
    let mut validation = Validation::new(alg);
    validation.set_issuer(&[issuer]);
    validation.set_audience(&[audience]);
    // Also reject not-yet-valid tokens; jsonwebtoken ignores `nbf` unless asked.
    // Everything else, including `exp` and its default leeway, is left as default.
    validation.validate_nbf = true;
    validation
}

fn decode_claims(token: &str, key: &DecodingKey, validation: &Validation) -> Result<Claims> {
    let mut claims = decode::<Claims>(token, key, validation)?.claims;
    token.clone_into(&mut claims.raw_token);
    if claims.ak_proxy.is_none() {
        claims.ak_proxy = Some(ProxyClaims::default());
    }
    Ok(claims)
}

/// Verify an HS256-signed token using the provider client secret.
pub(crate) fn verify_hs256(
    token: &str,
    secret: &str,
    issuer: &str,
    audience: &str,
) -> Result<Claims> {
    let key = DecodingKey::from_secret(secret.as_bytes());
    decode_claims(token, &key, &validation(Algorithm::HS256, issuer, audience))
}

/// Extract the `kid` from a token header without verifying the signature.
pub(crate) fn token_kid(token: &str) -> Result<Option<String>> {
    Ok(decode_header(token)?.kid)
}

/// Verify an RS256-signed token against the JWK matching its `kid`.
pub(crate) fn verify_rs256(
    token: &str,
    jwks: &JwkSet,
    issuer: &str,
    audience: &str,
) -> Result<Claims> {
    let kid = decode_header(token)?
        .kid
        .ok_or_else(|| eyre!("token header has no kid"))?;
    let jwk = jwks
        .find(&kid)
        .ok_or_else(|| eyre!("no JWK matching kid {kid}"))?;
    let key = DecodingKey::from_jwk(jwk)?;
    decode_claims(token, &key, &validation(Algorithm::RS256, issuer, audience))
}

#[cfg(test)]
mod tests {
    use std::time::{SystemTime, UNIX_EPOCH};

    use jsonwebtoken::{Algorithm, EncodingKey, Header, encode, jwk::JwkSet};
    use serde_json::{Value, json};

    use super::{verify_hs256, verify_rs256};

    const ISSUER: &str = "https://test.goauthentik.io/application/o/test-app/";
    const AUDIENCE: &str = "client-123";
    const KID: &str = "test-key";

    const RSA_PRIVATE_KEY: &str = "-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDxpRHguw7c8aa+
pCIdNtjBbDyARyVSyVl8QA8NVoeh5BHDf6uj3gS3YOcb5OY8wyzueDmJgof5TgRd
aYfmmEgxPc0YZF82AHf7liAuspEevhG5Ci5vFsPb5dbayyH4gpL9VxYGm8+fBPeB
UATBxeFqYQanK9wfmG4NRT1cthjrCLpwz0RnQjBblDmcZiSWXpy/9+hXR5dP07h6
cj78lwkSpMk0EFnZC9+7SthUWAGr7nZEXTVxHhs+d29R71213WAJCS64EIUNa6nR
3B83JISO4/yDWTqA96QO0QfV8OTNaWqUoKTrlVUF9kuB/r0hhAl2CnNYxa/7dkg+
5fGtkZRVAgMBAAECggEACr3xJdzmG+WX9igWOYqKlEvTNn5sw8aEvMydNRU7mZnQ
CorwCDlFqBnXVD32vszY81XmJ7B+vZ/dlLVGnKl4cuXukNvFzSdnetUXsHO9yao4
Rl7g2KcTeFpG7mCy0/KibAwokMBXuH42rkMuhVp37l89tdJx9xHMrJ7Y5Wu75Ype
hos2Wl5xwkxlQN1O4gcD1BIdCBjgU+DtP4N305T5OqOvcOuD7iW4Pd0Pk3VBHfH7
3Uchx1/qryf9N1yQ2/jTOR0vQmAILRLArbs8k93lX2eHgNjdNpBobDVYuC/1sfRH
cgXuTABlau/AdIYUPCvniHX+WLwntU5aVfgiFEbkWQKBgQD7F9LeOv0MaQf2FtYE
5thOFv6G/+YMccsBZWm9u2RX/5LOdsls9mvlHrc4+6nLj/+UXYFyYTBOGCaUYbs/
6q9T+0cMN9u8OhQ3w6u4xlyeTi3hyU+WvZC1zEYQuQ/aWumCyhTjXNpJCD91oVAT
BbUH9qSN9lCNaLoNWA5umoG/GQKBgQD2XfpkO40XZ4oX2mo5n0TElayF+nX1CZZL
p+ikxJQwOkOUhKXVzOKzXNSFUBfCnq1Fvp0azjpXRusf5TDDI0tThT2giujhj5X6
oGEZAO1mQmO3LehdxpKHe/KPCzXAFbxxxn9EjsVTevbdGBPouce/TYUZNofQDV4Y
HsvxoiCynQKBgQDUKrhKgcuqveE1RuyG7cyeh32A8yAfKdQglOG5qWtLlDAnd2YS
RVK8Iq0tYDGESWPrqOsljAv2ISAQR1ii1Jpbuzq4j0aEEQteZ19l3W8LcQICBEnV
FM7/XuFhZg6IMkOX+UuXJrFn/qkoqyrvN+ZVGUrIjfZY1sJHXj2rpbC2mQKBgDRE
m+rH95cPkGyfGgo/kAdk+cUy7fOepRRH+0N5sTbKJaxMuCIz5aTH/Q6Lf376yygQ
2KPnPNlnYlrR9RZxVnnRutFkpyOzos4ZWIBFghg/3YfvZWz/w/aahUtzxWOLOP+q
bTXOVG7xl44wnYiyYX5ko+hFeWraaywS3JHXI7jBAoGAKSMYA5t6gWbgwD0ZzwOB
sOnR1jOiuTTce05TQVUfnn8LT3I8dxi5QcVxNNf5cnfpDrObKtlHIzovXtXs9GA1
W9t+ndEPiB25CEiY+kschvSxDRjmnES2Dk5La8hVy/3RT//DySrwJDBbzxp5zwX7
J78973mJGC9/uRJqtkbPBeQ=
-----END PRIVATE KEY-----";

    const RSA_MODULUS: &str = "8aUR4LsO3PGmvqQiHTbYwWw8gEclUslZfEAPDVaHoeQRw3-ro94Et2DnG-TmPMMs7ng5iYKH-U4EXWmH5phIMT3NGGRfNgB3-5YgLrKRHr4RuQoubxbD2-XW2ssh-IKS_VcWBpvPnwT3gVAEwcXhamEGpyvcH5huDUU9XLYY6wi6cM9EZ0IwW5Q5nGYkll6cv_foV0eXT9O4enI-_JcJEqTJNBBZ2Qvfu0rYVFgBq-52RF01cR4bPndvUe9dtd1gCQkuuBCFDWup0dwfNySEjuP8g1k6gPekDtEH1fDkzWlqlKCk65VVBfZLgf69IYQJdgpzWMWv-3ZIPuXxrZGUVQ";

    fn now() -> u64 {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("system clock before unix epoch")
            .as_secs()
    }

    fn expiry() -> u64 {
        now() + 3_600_u64
    }

    fn hs256_token(claims: &Value) -> String {
        encode(
            &Header::new(Algorithm::HS256),
            claims,
            &EncodingKey::from_secret(b"client-secret"),
        )
        .expect("failed to sign token")
    }

    fn token_claims() -> Value {
        json!({
            "iss": ISSUER,
            "aud": AUDIENCE,
            "exp": expiry(),
            "sub": "user-uuid",
            "email": "user@example.com",
            "preferred_username": "akadmin",
            "groups": ["admins"],
        })
    }

    fn jwks() -> JwkSet {
        serde_json::from_value(json!({
            "keys": [{
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "kid": KID,
                "n": RSA_MODULUS,
                "e": "AQAB",
            }]
        }))
        .expect("failed to parse JWKS")
    }

    #[test]
    fn verifies_hs256() {
        let secret = "client-secret";
        let token = encode(
            &Header::new(Algorithm::HS256),
            &token_claims(),
            &EncodingKey::from_secret(secret.as_bytes()),
        )
        .expect("failed to sign token");

        let claims = verify_hs256(&token, secret, ISSUER, AUDIENCE).expect("verification failed");

        assert_eq!(claims.sub, "user-uuid");
        assert_eq!(claims.preferred_username, "akadmin");
        assert_eq!(claims.groups, vec!["admins".to_owned()]);
        assert_eq!(claims.raw_token, token);
        assert!(claims.ak_proxy.is_some());
    }

    #[test]
    fn verifies_rs256() {
        let mut header = Header::new(Algorithm::RS256);
        header.kid = Some(KID.to_owned());
        let token = encode(
            &header,
            &token_claims(),
            &EncodingKey::from_rsa_pem(RSA_PRIVATE_KEY.as_bytes()).expect("failed to load key"),
        )
        .expect("failed to sign token");

        let claims = verify_rs256(&token, &jwks(), ISSUER, AUDIENCE).expect("verification failed");

        assert_eq!(claims.sub, "user-uuid");
        assert_eq!(claims.raw_token, token);
        assert!(claims.ak_proxy.is_some());
    }

    #[test]
    fn rejects_wrong_issuer() {
        let secret = "client-secret";
        let token = encode(
            &Header::new(Algorithm::HS256),
            &token_claims(),
            &EncodingKey::from_secret(secret.as_bytes()),
        )
        .expect("failed to sign token");

        let _ = verify_hs256(&token, secret, "https://evil.example.com/", AUDIENCE)
            .expect_err("should reject mismatched issuer");
    }

    #[test]
    fn rejects_expired_token() {
        // Expired well beyond any leeway — confirms `exp` is still validated.
        let token = hs256_token(&json!({
            "iss": ISSUER, "aud": AUDIENCE, "sub": "user", "exp": now() - 3600,
        }));
        let _ = verify_hs256(&token, "client-secret", ISSUER, AUDIENCE)
            .expect_err("expired token must be rejected");
    }

    #[test]
    fn accepts_not_yet_valid_within_leeway() {
        // `nbf` slightly ahead is tolerated by jsonwebtoken's default leeway.
        let token = hs256_token(&json!({
            "iss": ISSUER, "aud": AUDIENCE, "sub": "user",
            "exp": now() + 3600, "nbf": now() + 30,
        }));
        verify_hs256(&token, "client-secret", ISSUER, AUDIENCE)
            .expect("nbf within the default leeway should be accepted");
    }

    #[test]
    fn rejects_not_yet_valid_beyond_leeway() {
        // `nbf` ten minutes ahead is well beyond the default leeway.
        let token = hs256_token(&json!({
            "iss": ISSUER, "aud": AUDIENCE, "sub": "user",
            "exp": now() + 3600, "nbf": now() + 600,
        }));
        let _ = verify_hs256(&token, "client-secret", ISSUER, AUDIENCE)
            .expect_err("nbf beyond the default leeway must be rejected");
    }

    #[test]
    fn rejects_unknown_kid() {
        let mut header = Header::new(Algorithm::RS256);
        header.kid = Some("other-key".to_owned());
        let token = encode(
            &header,
            &token_claims(),
            &EncodingKey::from_rsa_pem(RSA_PRIVATE_KEY.as_bytes()).expect("failed to load key"),
        )
        .expect("failed to sign token");

        let _ =
            verify_rs256(&token, &jwks(), ISSUER, AUDIENCE).expect_err("should reject unknown kid");
    }
}
