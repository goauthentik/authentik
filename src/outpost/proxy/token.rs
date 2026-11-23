//! Verification of authentik-issued access tokens (used as ID tokens).
//!
//! HS256 and RS256 tokens go through jsonwebtoken. ML-DSA tokens (RFC 9964) are
//! verified with aws-lc-rs directly, since jsonwebtoken has no post-quantum
//! algorithms and cannot even parse a header naming one.

use aws_lc_rs::signature::{
    ML_DSA_44, ML_DSA_65, ML_DSA_87, UnparsedPublicKey, VerificationAlgorithm,
};
use base64::{Engine as _, engine::general_purpose::URL_SAFE_NO_PAD as BASE64URL};
use eyre::{Result, bail, eyre};
use jsonwebtoken::{
    Algorithm, DecodingKey, Validation, decode, get_current_timestamp,
    jwk::{AlgorithmParameters, Jwk, JwkSet},
};
use serde::Deserialize;

use crate::outpost::proxy::claims::{Claims, ProxyClaims};

/// Leeway applied to `exp` and `nbf` on the ML-DSA path; matches jsonwebtoken's
/// default so both verification paths accept the same tokens.
const LEEWAY_SECONDS: u64 = 60;

fn validation(alg: Algorithm, issuer: &str, audience: &str) -> Validation {
    let mut validation = Validation::new(alg);
    validation.set_issuer(&[issuer]);
    validation.set_audience(&[audience]);
    // Require `exp`, `aud` and `iss`: jsonwebtoken only checks the issuer and
    // audience when those claims are present, so without this a token omitting
    // them would pass verification.
    validation.set_required_spec_claims(&["exp", "aud", "iss"]);
    // Reject not-yet-valid tokens; jsonwebtoken ignores `nbf` unless asked.
    validation.validate_nbf = true;
    validation
}

fn decode_claims(token: &str, key: &DecodingKey, validation: &Validation) -> Result<Claims> {
    let claims = decode::<Claims>(token, key, validation)?.claims;
    Ok(finish_claims(token, claims))
}

fn finish_claims(token: &str, mut claims: Claims) -> Claims {
    token.clone_into(&mut claims.raw_token);
    if claims.ak_proxy.is_none() {
        claims.ak_proxy = Some(ProxyClaims::default());
    }
    claims
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

/// The header fields needed to route a token, parsed without jsonwebtoken so
/// that an `alg` it does not know (ML-DSA) still gets through.
#[derive(Deserialize)]
struct RawHeader {
    alg: String,
    kid: Option<String>,
}

fn raw_header(token: &str) -> Result<RawHeader> {
    let header = token
        .split('.')
        .next()
        .ok_or_else(|| eyre!("malformed token"))?;
    Ok(serde_json::from_slice(&BASE64URL.decode(header)?)?)
}

/// Extract the `kid` from a token header without verifying the signature.
pub(crate) fn token_kid(token: &str) -> Result<Option<String>> {
    Ok(raw_header(token)?.kid)
}

fn mldsa_algorithm(alg: &str) -> Option<&'static dyn VerificationAlgorithm> {
    match alg {
        "ML-DSA-44" => Some(&ML_DSA_44),
        "ML-DSA-65" => Some(&ML_DSA_65),
        "ML-DSA-87" => Some(&ML_DSA_87),
        _ => None,
    }
}

/// Verify a token signed with the provider's key pair against the JWK matching
/// its `kid`: RS256 through jsonwebtoken, ML-DSA through aws-lc-rs.
pub(crate) fn verify_jwks(
    token: &str,
    jwks: &JwkSet,
    issuer: &str,
    audience: &str,
) -> Result<Claims> {
    let header = raw_header(token)?;
    let kid = header.kid.ok_or_else(|| eyre!("token header has no kid"))?;
    let jwk = jwks
        .find(&kid)
        .ok_or_else(|| eyre!("no JWK matching kid {kid}"))?;
    if let Some(algorithm) = mldsa_algorithm(&header.alg) {
        return verify_mldsa(token, jwk, &header.alg, algorithm, issuer, audience);
    }
    let key = DecodingKey::from_jwk(jwk)?;
    decode_claims(token, &key, &validation(Algorithm::RS256, issuer, audience))
}

/// The registered claims checked on the ML-DSA path, mirroring what
/// `validation` asks jsonwebtoken to enforce.
#[derive(Deserialize)]
struct RegisteredClaims {
    exp: Option<u64>,
    nbf: Option<u64>,
    iss: Option<String>,
    aud: Option<Audience>,
}

#[derive(Deserialize)]
#[serde(untagged)]
enum Audience {
    Single(String),
    Multiple(Vec<String>),
}

impl Audience {
    fn contains(&self, audience: &str) -> bool {
        match self {
            Self::Single(aud) => aud == audience,
            Self::Multiple(auds) => auds.iter().any(|aud| aud == audience),
        }
    }
}

/// Verify an ML-DSA (RFC 9964) signed token against an `AKP` JWK.
fn verify_mldsa(
    token: &str,
    jwk: &Jwk,
    alg: &str,
    algorithm: &'static dyn VerificationAlgorithm,
    issuer: &str,
    audience: &str,
) -> Result<Claims> {
    // jsonwebtoken keeps key types it does not know as a bag of fields.
    let AlgorithmParameters::Other(params) = &jwk.algorithm else {
        bail!("JWK for {alg} token is not an AKP key");
    };
    if params.fields.get("kty").and_then(serde_json::Value::as_str) != Some("AKP") {
        bail!("JWK for {alg} token is not an AKP key");
    }
    if let Some(jwk_alg) = params.fields.get("alg").and_then(serde_json::Value::as_str)
        && jwk_alg != alg
    {
        bail!("JWK algorithm {jwk_alg} does not match token algorithm {alg}");
    }
    let public_key = params
        .fields
        .get("pub")
        .and_then(serde_json::Value::as_str)
        .map(|encoded| BASE64URL.decode(encoded))
        .ok_or_else(|| eyre!("AKP JWK has no pub member"))??;

    let (message, signature) = token
        .rsplit_once('.')
        .ok_or_else(|| eyre!("malformed token"))?;
    let signature = BASE64URL.decode(signature)?;
    UnparsedPublicKey::new(algorithm, public_key)
        .verify(message.as_bytes(), &signature)
        .map_err(|_| eyre!("invalid {alg} signature"))?;

    let (_, payload) = message
        .split_once('.')
        .ok_or_else(|| eyre!("malformed token"))?;
    let payload = BASE64URL.decode(payload)?;
    validate_registered_claims(&serde_json::from_slice(&payload)?, issuer, audience)?;
    Ok(finish_claims(token, serde_json::from_slice(&payload)?))
}

fn validate_registered_claims(
    claims: &RegisteredClaims,
    issuer: &str,
    audience: &str,
) -> Result<()> {
    let now = get_current_timestamp();
    match claims.exp {
        Some(exp) if exp + LEEWAY_SECONDS >= now => {}
        Some(_) => bail!("token has expired"),
        None => bail!("token has no exp claim"),
    }
    if let Some(nbf) = claims.nbf
        && nbf > now + LEEWAY_SECONDS
    {
        bail!("token is not yet valid");
    }
    match claims.iss.as_deref() {
        Some(iss) if iss == issuer => {}
        Some(_) => bail!("token issuer does not match"),
        None => bail!("token has no iss claim"),
    }
    match &claims.aud {
        Some(aud) if aud.contains(audience) => Ok(()),
        Some(_) => bail!("token audience does not match"),
        None => bail!("token has no aud claim"),
    }
}

#[cfg(test)]
mod tests {
    use std::time::{SystemTime, UNIX_EPOCH};

    use aws_lc_rs::signature::{
        KeyPair as _, ML_DSA_44_SIGNING, ML_DSA_65_SIGNING, PqdsaKeyPair, PqdsaSigningAlgorithm,
    };
    use base64::{Engine as _, engine::general_purpose::URL_SAFE_NO_PAD as BASE64URL};
    use jsonwebtoken::{Algorithm, EncodingKey, Header, encode, jwk::JwkSet};
    use serde_json::{Value, json};

    use super::{verify_hs256, verify_jwks};

    const ISSUER: &str = "https://test.goauthentik.io/application/o/test-app/";
    const AUDIENCE: &str = "client-123";
    const KID: &str = "test-key";

    // spell-checker: disable
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
    // spell-checker: enable

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

    // spell-checker: disable
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
    // spell-checker: enable

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

        let claims = verify_jwks(&token, &jwks(), ISSUER, AUDIENCE).expect("verification failed");

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
    fn rejects_missing_audience() {
        let token = hs256_token(&json!({
            "iss": ISSUER, "sub": "user", "exp": expiry(),
        }));
        let _ = verify_hs256(&token, "client-secret", ISSUER, AUDIENCE)
            .expect_err("token without aud must be rejected");
    }

    #[test]
    fn rejects_missing_issuer() {
        let token = hs256_token(&json!({
            "aud": AUDIENCE, "sub": "user", "exp": expiry(),
        }));
        let _ = verify_hs256(&token, "client-secret", ISSUER, AUDIENCE)
            .expect_err("token without iss must be rejected");
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
            verify_jwks(&token, &jwks(), ISSUER, AUDIENCE).expect_err("should reject unknown kid");
    }

    const MLDSA_KID: &str = "mldsa-key";

    fn mldsa_jwks(key_pair: &PqdsaKeyPair, alg: &str) -> JwkSet {
        serde_json::from_value(json!({
            "keys": [{
                "kty": "AKP",
                "use": "sig",
                "alg": alg,
                "kid": MLDSA_KID,
                "pub": BASE64URL.encode(key_pair.public_key().as_ref()),
            }]
        }))
        .expect("failed to parse JWKS")
    }

    fn mldsa_token(
        key_pair: &PqdsaKeyPair,
        signing: &PqdsaSigningAlgorithm,
        alg: &str,
        claims: &Value,
    ) -> String {
        let header =
            BASE64URL.encode(json!({"alg": alg, "kid": MLDSA_KID, "typ": "JWT"}).to_string());
        let payload = BASE64URL.encode(claims.to_string());
        let message = format!("{header}.{payload}");
        let mut signature = vec![0_u8; signing.signature_len()];
        let len = key_pair
            .sign(message.as_bytes(), &mut signature)
            .expect("failed to sign token");
        signature.truncate(len);
        format!("{message}.{}", BASE64URL.encode(signature))
    }

    #[test]
    fn verifies_mldsa() {
        for (signing, alg) in [
            (&ML_DSA_44_SIGNING, "ML-DSA-44"),
            (&ML_DSA_65_SIGNING, "ML-DSA-65"),
        ] {
            let key_pair = PqdsaKeyPair::generate(signing).expect("failed to generate key");
            let token = mldsa_token(&key_pair, signing, alg, &token_claims());

            let claims = verify_jwks(&token, &mldsa_jwks(&key_pair, alg), ISSUER, AUDIENCE)
                .expect("verification failed");

            assert_eq!(claims.sub, "user-uuid");
            assert_eq!(claims.preferred_username, "akadmin");
            assert_eq!(claims.groups, vec!["admins".to_owned()]);
            assert_eq!(claims.raw_token, token);
            assert!(claims.ak_proxy.is_some());
        }
    }

    #[test]
    fn rejects_mldsa_wrong_key() {
        let signer = PqdsaKeyPair::generate(&ML_DSA_44_SIGNING).expect("failed to generate key");
        let other = PqdsaKeyPair::generate(&ML_DSA_44_SIGNING).expect("failed to generate key");
        let token = mldsa_token(&signer, &ML_DSA_44_SIGNING, "ML-DSA-44", &token_claims());

        let _ = verify_jwks(&token, &mldsa_jwks(&other, "ML-DSA-44"), ISSUER, AUDIENCE)
            .expect_err("signature from another key must be rejected");
    }

    #[test]
    fn rejects_mldsa_tampered_payload() {
        let key_pair = PqdsaKeyPair::generate(&ML_DSA_44_SIGNING).expect("failed to generate key");
        let token = mldsa_token(&key_pair, &ML_DSA_44_SIGNING, "ML-DSA-44", &token_claims());
        let (header, rest) = token.split_once('.').expect("malformed token");
        let (_, signature) = rest.rsplit_once('.').expect("malformed token");
        let payload = BASE64URL.encode(
            json!({
                "iss": ISSUER, "aud": AUDIENCE, "exp": expiry(), "sub": "someone-else",
            })
            .to_string(),
        );
        let tampered = format!("{header}.{payload}.{signature}");

        let _ = verify_jwks(
            &tampered,
            &mldsa_jwks(&key_pair, "ML-DSA-44"),
            ISSUER,
            AUDIENCE,
        )
        .expect_err("tampered payload must be rejected");
    }

    #[test]
    fn rejects_mldsa_algorithm_mismatch() {
        // The token names a different parameter set than the JWK it references.
        let key_pair = PqdsaKeyPair::generate(&ML_DSA_44_SIGNING).expect("failed to generate key");
        let token = mldsa_token(&key_pair, &ML_DSA_44_SIGNING, "ML-DSA-65", &token_claims());

        let _ = verify_jwks(
            &token,
            &mldsa_jwks(&key_pair, "ML-DSA-44"),
            ISSUER,
            AUDIENCE,
        )
        .expect_err("algorithm mismatch must be rejected");
    }

    #[test]
    fn rejects_mldsa_with_rsa_jwk() {
        let key_pair = PqdsaKeyPair::generate(&ML_DSA_44_SIGNING).expect("failed to generate key");
        let claims = token_claims();
        let header = BASE64URL.encode(json!({"alg": "ML-DSA-44", "kid": KID}).to_string());
        let payload = BASE64URL.encode(claims.to_string());
        let message = format!("{header}.{payload}");
        let mut signature = vec![0_u8; ML_DSA_44_SIGNING.signature_len()];
        let len = key_pair
            .sign(message.as_bytes(), &mut signature)
            .expect("failed to sign token");
        signature.truncate(len);
        let token = format!("{message}.{}", BASE64URL.encode(signature));

        let _ = verify_jwks(&token, &jwks(), ISSUER, AUDIENCE)
            .expect_err("an RSA JWK cannot verify an ML-DSA token");
    }

    #[test]
    fn rejects_mldsa_expired_and_wrong_issuer() {
        let key_pair = PqdsaKeyPair::generate(&ML_DSA_44_SIGNING).expect("failed to generate key");
        let jwks = mldsa_jwks(&key_pair, "ML-DSA-44");
        let expired = mldsa_token(
            &key_pair,
            &ML_DSA_44_SIGNING,
            "ML-DSA-44",
            &json!({"iss": ISSUER, "aud": AUDIENCE, "sub": "user", "exp": now() - 3600}),
        );
        let _ = verify_jwks(&expired, &jwks, ISSUER, AUDIENCE)
            .expect_err("expired token must be rejected");

        let valid = mldsa_token(&key_pair, &ML_DSA_44_SIGNING, "ML-DSA-44", &token_claims());
        let _ = verify_jwks(&valid, &jwks, "https://evil.example.com/", AUDIENCE)
            .expect_err("mismatched issuer must be rejected");
        let _ = verify_jwks(&valid, &jwks, ISSUER, "other-client")
            .expect_err("mismatched audience must be rejected");

        let missing_aud = mldsa_token(
            &key_pair,
            &ML_DSA_44_SIGNING,
            "ML-DSA-44",
            &json!({"iss": ISSUER, "sub": "user", "exp": expiry()}),
        );
        let _ = verify_jwks(&missing_aud, &jwks, ISSUER, AUDIENCE)
            .expect_err("token without aud must be rejected");

        let not_yet_valid = mldsa_token(
            &key_pair,
            &ML_DSA_44_SIGNING,
            "ML-DSA-44",
            &json!({"iss": ISSUER, "aud": AUDIENCE, "sub": "user", "exp": expiry(), "nbf": now() + 600}),
        );
        let _ = verify_jwks(&not_yet_valid, &jwks, ISSUER, AUDIENCE)
            .expect_err("nbf beyond leeway must be rejected");
    }
}
