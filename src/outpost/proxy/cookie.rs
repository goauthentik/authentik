//! Signed session-ID cookie handling.

use std::fmt;
use std::time::Duration;

use aws_lc_rs::digest;
use axum::http::HeaderMap;
use axum_extra::extract::cookie::{Cookie, Key, SameSite, SignedCookieJar};
use eyre::{Result, eyre};

/// Per-provider signed cookie carrying the opaque session ID.
pub(crate) struct SessionCookie {
    key: Key,
    name: String,
    secure: bool,
    domain: Option<String>,
}

impl fmt::Debug for SessionCookie {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("SessionCookie")
            .field("name", &self.name)
            .field("secure", &self.secure)
            .field("domain", &self.domain)
            .finish_non_exhaustive()
    }
}

impl SessionCookie {
    pub(crate) fn new(
        client_id: &str,
        cookie_secret: &str,
        secure: bool,
        domain: Option<String>,
    ) -> Result<Self> {
        if cookie_secret.len() < 32 {
            return Err(eyre!("cookie secret must be at least 32 bytes"));
        }
        Ok(Self {
            key: Key::derive_from(cookie_secret.as_bytes()),
            name: cookie_name(client_id),
            secure,
            domain: domain.filter(|domain| !domain.is_empty()),
        })
    }

    /// Build a signed cookie jar from the request headers.
    pub(crate) fn jar(&self, headers: &HeaderMap) -> SignedCookieJar {
        SignedCookieJar::from_headers(headers, self.key.clone())
    }

    /// Read and verify the session ID from a signed cookie jar.
    pub(crate) fn read(&self, jar: &SignedCookieJar) -> Option<String> {
        jar.get(&self.name).map(|cookie| cookie.value().to_owned())
    }

    /// Build a cookie that clears the session cookie in the browser.
    pub(crate) fn removal(&self) -> Cookie<'static> {
        let mut cookie = Cookie::new(self.name.clone(), "");
        cookie.set_path("/");
        if let Some(domain) = &self.domain {
            cookie.set_domain(domain.clone());
        }
        cookie
    }

    /// Build the cookie carrying `sid`, valid for `max_age`.
    pub(crate) fn build(&self, sid: &str, max_age: Duration) -> Cookie<'static> {
        let mut cookie = Cookie::new(self.name.clone(), sid.to_owned());
        cookie.set_http_only(true);
        cookie.set_secure(self.secure);
        cookie.set_same_site(SameSite::Lax);
        cookie.set_path("/");
        if let Some(domain) = &self.domain {
            cookie.set_domain(domain.clone());
        }
        cookie.set_max_age(time::Duration::try_from(max_age).unwrap_or(time::Duration::ZERO));
        cookie
    }
}

/// `authentik_proxy_<first 4 bytes of sha256(client_id), hex>`.
fn cookie_name(client_id: &str) -> String {
    use std::fmt::Write as _;

    let hash = digest::digest(&digest::SHA256, client_id.as_bytes());
    let mut name = "authentik_proxy_".to_owned();
    for byte in hash.as_ref().iter().take(4) {
        let _ = write!(name, "{byte:02x}");
    }
    name
}

#[cfg(test)]
mod tests {
    use std::time::Duration;

    use axum::http::{HeaderMap, header};
    use axum::response::IntoResponse as _;

    use super::{SessionCookie, cookie_name};

    // 32-byte secret (matches authentik's generated cookie secret length).
    const SECRET: &str = "0123456789abcdef0123456789abcdef";

    fn issued_set_cookie(cookie: &SessionCookie, sid: &str) -> String {
        let jar = cookie.jar(&HeaderMap::new()).add(cookie.build(sid, Duration::from_mins(1)));
        let response = (jar, ()).into_response();
        response
            .headers()
            .get(header::SET_COOKIE)
            .expect("set-cookie header")
            .to_str()
            .expect("utf-8 header")
            .to_owned()
    }

    #[test]
    fn round_trip_signed_cookie() {
        let cookie =
            SessionCookie::new("client-123", SECRET, true, Some("example.com".to_owned()))
                .expect("session cookie");

        let set_cookie = issued_set_cookie(&cookie, "the-sid");
        let pair = set_cookie.split(';').next().expect("name=value pair");

        let mut headers = HeaderMap::new();
        headers.insert(header::COOKIE, pair.parse().expect("cookie header value"));

        assert_eq!(cookie.read(&cookie.jar(&headers)), Some("the-sid".to_owned()));
    }

    #[test]
    fn sets_expected_attributes() {
        let cookie =
            SessionCookie::new("client-123", SECRET, true, Some("example.com".to_owned()))
                .expect("session cookie");
        let set_cookie = issued_set_cookie(&cookie, "the-sid");

        assert!(set_cookie.contains("HttpOnly"));
        assert!(set_cookie.contains("Secure"));
        assert!(set_cookie.contains("SameSite=Lax"));
        assert!(set_cookie.contains("Path=/"));
        assert!(set_cookie.contains("Domain=example.com"));
    }

    #[test]
    fn rejects_wrong_key() {
        let writer =
            SessionCookie::new("client-123", SECRET, false, None).expect("session cookie");
        let reader =
            SessionCookie::new("client-123", "ffffffffffffffffffffffffffffffff", false, None)
                .expect("session cookie");

        let set_cookie = issued_set_cookie(&writer, "the-sid");
        let pair = set_cookie.split(';').next().expect("name=value pair");
        let mut headers = HeaderMap::new();
        headers.insert(header::COOKIE, pair.parse().expect("cookie header value"));

        assert_eq!(reader.read(&reader.jar(&headers)), None);
    }

    #[test]
    fn short_secret_is_rejected() {
        let _ = SessionCookie::new("client-123", "too-short", false, None)
            .expect_err("secret under 32 bytes should be rejected");
    }

    #[test]
    fn cookie_name_is_stable_and_prefixed() {
        let name = cookie_name("client-123");
        assert!(name.starts_with("authentik_proxy_"));
        assert_eq!(name, cookie_name("client-123"));
        assert_ne!(name, cookie_name("client-456"));
    }
}
