use std::fmt::Write as _;

use aws_lc_rs::digest;
use axum::{
    Router,
    extract::{Query, Request, State},
    http::{
        HeaderMap, HeaderValue, StatusCode,
        header::{CACHE_CONTROL, CONTENT_ENCODING, CONTENT_SECURITY_POLICY, ETAG, VARY},
    },
    middleware::{self, Next},
    response::{IntoResponse as _, Response},
    routing::any,
};
use jsonwebtoken::{Algorithm, DecodingKey, Validation, decode, decode_header};
use percent_encoding::percent_decode_str;
use serde::Deserialize;
use time::OffsetDateTime;
use tower_http::{
    compression::{CompressionLayer, predicate::SizeAbove},
    services::fs::ServeDir,
};

use crate::config;

#[derive(Debug, Deserialize)]
struct StorageClaims {
    exp: Option<i64>,
    nbf: Option<i64>,
    path: Option<String>,
}

#[derive(Debug, Deserialize)]
struct StorageTokenQuery {
    token: Option<String>,
}

fn is_storage_token_valid(usage: &str, secret_key: &str, request: &Request) -> bool {
    // Use typed query parsing so `token` is percent-decoded before JWT parsing.
    let token_string = match Query::<StorageTokenQuery>::try_from_uri(request.uri()) {
        Ok(query) => match query.0.token {
            Some(token) if !token.is_empty() => token,
            _ => return false,
        },
        Err(_) => return false,
    };

    let Ok(token_header) = decode_header(&token_string) else {
        return false;
    };

    // Must match what we use in authentik/admin/files/backends/file.py
    if token_header.alg != Algorithm::HS256 {
        return false;
    }

    // Derive a per-usage key so media and reports tokens are not interchangeable.
    let key = format!("{secret_key}:{usage}");
    let key_digest = digest::digest(&digest::SHA256, key.as_bytes());
    let key_hex_digest = key_digest
        .as_ref()
        .iter()
        .fold(String::new(), |mut acc, b| {
            let _ = write!(acc, "{b:02x}");
            acc
        });

    let mut validation = Validation::new(token_header.alg);
    validation.validate_exp = false;
    validation.validate_nbf = false;
    validation.validate_aud = false;
    validation.required_spec_claims.clear();

    let claims = match decode::<StorageClaims>(
        &token_string,
        &DecodingKey::from_secret(key_hex_digest.as_bytes()),
        &validation,
    ) {
        Ok(token) => token.claims,
        Err(_) => return false,
    };

    let now = OffsetDateTime::now_utc().unix_timestamp();
    if claims.exp.unwrap_or(0) < now {
        return false;
    }
    if claims.nbf.unwrap_or(now + 1) > now {
        return false;
    }

    let Some(claim_path) = claims.path else {
        return false;
    };
    // Decode path before comparison so encoded URL segments cannot bypass path binding.
    let Ok(request_path) = percent_decode_str(request.uri().path()).decode_utf8() else {
        return false;
    };
    let request_path = request_path.trim_start_matches('/');
    let expected_path = format!("{usage}/{request_path}");
    if claim_path != expected_path {
        return false;
    }

    true
}

#[derive(Clone)]
struct StorageMiddlewareConfig {
    usage: &'static str,
    set_csp_header: bool,
}

async fn storage_middleware(
    State(config): State<StorageMiddlewareConfig>,
    request: Request,
    next: Next,
) -> Response {
    if !is_storage_token_valid(config.usage, &config::get().secret_key, &request) {
        return (StatusCode::NOT_FOUND, "404 page not found\n").into_response();
    }

    let mut response = next.run(request).await;

    if config.set_csp_header {
        // Since media is user-controlled, better be safe
        response.headers_mut().insert(
            CONTENT_SECURITY_POLICY,
            HeaderValue::from_static("default-src 'none'; style-src 'unsafe-inline'; sandbox"),
        );
    }

    response
}

async fn static_header_middleware(request: Request, next: Next) -> Response {
    let mut response = next.run(request).await;

    response.headers_mut().insert(
        CACHE_CONTROL,
        HeaderValue::from_static("public, no-transform"),
    );
    response.headers_mut().insert(
        "X-authentik-version",
        HeaderValue::from_static(env!("CARGO_PKG_VERSION")),
    );

    response
}

/// Trim leading and trailing optional whitespace, as defined by RFC 9110 §5.6.3.
fn trim_ows(value: &[u8]) -> &[u8] {
    let is_ows = |byte: &u8| matches!(*byte, b' ' | b'\t');
    let start = value.iter().position(|byte| !is_ows(byte));
    let end = value.iter().rposition(|byte| !is_ows(byte));
    match (start, end) {
        (Some(start), Some(end)) => value.get(start..=end).unwrap_or_default(),
        _ => &[],
    }
}

/// Whether `Vary` already accounts for `Accept-Encoding`.
fn varies_on_accept_encoding(headers: &HeaderMap) -> bool {
    headers.get_all(VARY).iter().any(|value| {
        value
            .as_bytes()
            .split(|byte| *byte == b',')
            .map(trim_ows)
            .any(|field| field == b"*" || field.eq_ignore_ascii_case(b"accept-encoding"))
    })
}

/// Whether a content-coding other than `identity` was applied to the body.
fn has_content_coding(headers: &HeaderMap) -> bool {
    headers.get_all(CONTENT_ENCODING).iter().any(|value| {
        value
            .as_bytes()
            .split(|byte| *byte == b',')
            .map(trim_ows)
            .any(|coding| !coding.is_empty() && !coding.eq_ignore_ascii_case(b"identity"))
    })
}

/// Downgrade a strong entity-tag to a weak one, leaving the opaque-tag intact.
fn weaken_etag(headers: &mut HeaderMap) {
    let Some(etag) = headers.get(ETAG) else {
        return;
    };
    if etag.as_bytes().starts_with(b"W/") {
        return;
    }

    let mut weak = Vec::with_capacity(etag.len() + 2);
    weak.extend_from_slice(b"W/");
    weak.extend_from_slice(etag.as_bytes());
    if let Ok(weak) = HeaderValue::from_bytes(&weak) {
        headers.insert(ETAG, weak);
    }
}

/// Repair the content-negotiation headers of a response that has already been
/// through [`compression_layer`].
///
/// This has to sit *outside* the compression layer, because it needs to observe
/// the `Content-Encoding` that was actually negotiated.
async fn negotiated_representation_middleware(request: Request, next: Next) -> Response {
    let mut response = next.run(request).await;
    let headers = response.headers_mut();

    // RFC 9110 §15.4.5 requires a 304 to carry the header fields that the
    // corresponding 200 would have carried, and names `Vary` explicitly.
    // `CompressionLayer` appends `Vary` only when it encodes a body, so a
    // bodiless 304 loses it and a shared cache ends up storing every coding
    // under a single key.
    if !varies_on_accept_encoding(headers) {
        headers.append(VARY, HeaderValue::from_static("accept-encoding"));
    }

    // A content-coding is part of the representation (RFC 9110 §8.4.1), so one
    // strong validator must not label both the identity bytes and the encoded
    // bytes (RFC 9110 §8.8.1). `ServeDir` derives the tag from file metadata
    // and cannot know that the response was encoded afterwards, so weaken it
    // here, the way nginx does. Weak comparison (RFC 9110 §13.1.2) is what
    // `If-None-Match` uses, so revalidation keeps working.
    if has_content_coding(headers) {
        weaken_etag(headers);
    }

    response
}

fn compression_layer() -> CompressionLayer<SizeAbove> {
    CompressionLayer::new().compress_when(SizeAbove::new(32))
}

pub(crate) fn build_router() -> Router {
    let config = config::get();

    let mut router = Router::new().layer(middleware::from_fn(static_header_middleware));

    let dist_fs = ServeDir::new("./web/dist/").append_index_html_on_directories(false);
    let static_fs = ServeDir::new("./web/authentik/").append_index_html_on_directories(false);

    router = router.nest_service("/static/dist/", dist_fs.clone());
    router = router.nest_service("/static/authentik/", static_fs);

    router = router.nest_service("/if/flow/{flow_slug}/assets/", dist_fs.clone());
    router = router.nest_service("/if/admin/assets/", dist_fs.clone());
    router = router.nest_service("/if/user/assets/", dist_fs.clone());
    router = router.nest_service("/if/rac/{app_slug}/assets/", dist_fs);

    let default_backend = &config.storage.backend;
    let media_backend = config
        .storage
        .media
        .clone()
        .unwrap_or_default()
        .backend
        .unwrap_or_else(|| default_backend.clone());
    let reports_backend = config
        .storage
        .reports
        .clone()
        .unwrap_or_default()
        .backend
        .unwrap_or_else(|| default_backend.clone());

    let default_path = &config.storage.file.path;

    if media_backend == "file" {
        let media_path = config
            .storage
            .media
            .clone()
            .unwrap_or_default()
            .file
            .unwrap_or_default()
            .path
            .unwrap_or_else(|| default_path.clone())
            .join("media");

        let media_fs = ServeDir::new(media_path).append_index_html_on_directories(false);
        let media_router =
            Router::new()
                .fallback_service(media_fs)
                .layer(middleware::from_fn_with_state(
                    StorageMiddlewareConfig {
                        usage: "media",
                        set_csp_header: true,
                    },
                    storage_middleware,
                ));
        router = router.nest("/files/media/", media_router);
    }

    if reports_backend == "file" {
        let reports_path = config
            .storage
            .reports
            .clone()
            .unwrap_or_default()
            .file
            .unwrap_or_default()
            .path
            .unwrap_or_else(|| default_path.clone())
            .join("reports");

        let reports_fs = ServeDir::new(reports_path).append_index_html_on_directories(false);
        let reports_router =
            Router::new()
                .fallback_service(reports_fs)
                .layer(middleware::from_fn_with_state(
                    StorageMiddlewareConfig {
                        usage: "reports",
                        set_csp_header: false,
                    },
                    storage_middleware,
                ));
        router = router.nest("/files/reports/", reports_router);
    }

    router = router.route(
        "/robots.txt",
        any(async || include_str!("../../web/robots.txt")),
    );
    router = router.route(
        "/.well-known/security.txt",
        any(async || include_str!("../../web/security.txt")),
    );

    router = router.layer(middleware::from_fn(static_header_middleware));

    router = router.layer(compression_layer());

    // Outside the compression layer: it inspects the negotiated `Content-Encoding`.
    router = router.layer(middleware::from_fn(negotiated_representation_middleware));

    router
}

#[cfg(test)]
mod tests {
    use axum::{
        Router,
        body::Body,
        extract::Request,
        http::{
            StatusCode,
            header::{
                ACCEPT_ENCODING, CONTENT_ENCODING, CONTENT_LENGTH, CONTENT_RANGE, ETAG,
                IF_NONE_MATCH, RANGE, VARY,
            },
        },
        middleware,
    };
    use http_body_util::BodyExt as _;
    use tempfile::{TempDir, tempdir};
    use tokio::fs;
    use tower::ServiceExt as _;
    use tower_http::services::fs::ServeDir;

    use super::{compression_layer, negotiated_representation_middleware};

    /// Enough bytes to clear the `SizeAbove` threshold, and compressible enough
    /// that gzip is a visible win.
    const BODY: &[u8] = &[b'a'; 4096];

    /// Mirrors how [`build_router`] serves `/static/dist/`: a `ServeDir` under
    /// the shared compression layer, with the representation fix-ups layered
    /// outside it.
    fn router(dir: &TempDir) -> Router {
        Router::new()
            .nest_service(
                "/static/dist/",
                ServeDir::new(dir.path()).append_index_html_on_directories(false),
            )
            .layer(compression_layer())
            .layer(middleware::from_fn(negotiated_representation_middleware))
    }

    /// A plain `GET` for the fixture, announcing `accept-encoding`.
    fn get(accept_encoding: &str) -> axum::http::request::Builder {
        Request::builder()
            .uri("/static/dist/basemap.bin")
            .header(ACCEPT_ENCODING, accept_encoding)
    }

    /// Read the `ETag` of a response as a `String`.
    fn etag_of<B>(response: &axum::http::Response<B>) -> String {
        response
            .headers()
            .get(ETAG)
            .expect("missing ETag")
            .to_str()
            .expect("non-ASCII ETag")
            .to_owned()
    }

    async fn fixture() -> TempDir {
        let dir = tempdir().expect("failed to create temp dir");
        fs::write(dir.path().join("basemap.bin"), BODY)
            .await
            .expect("failed to write fixture");
        dir
    }

    #[tokio::test]
    async fn ranged_request_is_not_compressed() {
        let dir = fixture().await;
        let response = router(&dir)
            .oneshot(
                Request::builder()
                    .uri("/static/dist/basemap.bin")
                    .header(RANGE, "bytes=0-15")
                    .header(ACCEPT_ENCODING, "gzip")
                    .body(Body::empty())
                    .expect("failed to build request"),
            )
            .await
            .expect("request failed");

        assert_eq!(response.status(), StatusCode::PARTIAL_CONTENT);
        assert_eq!(
            response
                .headers()
                .get(CONTENT_RANGE)
                .expect("missing Content-Range"),
            "bytes 0-15/4096"
        );
        // A compressed 206 would describe the encoded length, not the range.
        assert_eq!(
            response
                .headers()
                .get(CONTENT_LENGTH)
                .expect("missing Content-Length"),
            "16"
        );
        assert!(
            response.headers().get(CONTENT_ENCODING).is_none(),
            "ranged response must not be re-encoded"
        );

        let body = response
            .into_body()
            .collect()
            .await
            .expect("failed to read body")
            .to_bytes();
        assert_eq!(&body[..], &BODY[..16]);
    }

    #[tokio::test]
    async fn full_request_is_still_compressed() {
        let dir = fixture().await;
        let response = router(&dir)
            .oneshot(
                Request::builder()
                    .uri("/static/dist/basemap.bin")
                    .header(ACCEPT_ENCODING, "gzip")
                    .body(Body::empty())
                    .expect("failed to build request"),
            )
            .await
            .expect("request failed");

        assert_eq!(response.status(), StatusCode::OK);
        assert_eq!(
            response
                .headers()
                .get(CONTENT_ENCODING)
                .expect("missing Content-Encoding"),
            "gzip"
        );
    }

    #[tokio::test]
    async fn encoded_response_weakens_the_etag() {
        let dir = fixture().await;

        let identity = router(&dir)
            .oneshot(
                get("identity")
                    .body(Body::empty())
                    .expect("failed to build request"),
            )
            .await
            .expect("request failed");

        assert_eq!(identity.status(), StatusCode::OK);
        assert!(
            identity.headers().get(CONTENT_ENCODING).is_none(),
            "identity response must not be encoded"
        );
        let strong = etag_of(&identity);
        assert!(
            !strong.starts_with("W/"),
            "unencoded representation keeps a strong validator, got {strong}"
        );

        let compressed = router(&dir)
            .oneshot(
                get("gzip")
                    .body(Body::empty())
                    .expect("failed to build request"),
            )
            .await
            .expect("request failed");

        assert_eq!(compressed.status(), StatusCode::OK);
        assert_eq!(
            compressed
                .headers()
                .get(CONTENT_ENCODING)
                .expect("missing Content-Encoding"),
            "gzip"
        );
        // The encoded bytes are a different representation, so the same strong
        // validator must not label both.
        assert_eq!(etag_of(&compressed), format!("W/{strong}"));
        // `CompressionLayer` already set `Vary` here; it must not be duplicated.
        assert_eq!(compressed.headers().get_all(VARY).iter().count(), 1);
    }

    #[tokio::test]
    async fn not_modified_response_keeps_vary() {
        let dir = fixture().await;

        let fresh = router(&dir)
            .oneshot(
                get("identity")
                    .body(Body::empty())
                    .expect("failed to build request"),
            )
            .await
            .expect("request failed");

        assert_eq!(fresh.status(), StatusCode::OK);
        let etag = etag_of(&fresh);

        let revalidated = router(&dir)
            .oneshot(
                get("identity")
                    .header(IF_NONE_MATCH, etag.as_str())
                    .body(Body::empty())
                    .expect("failed to build request"),
            )
            .await
            .expect("request failed");

        assert_eq!(revalidated.status(), StatusCode::NOT_MODIFIED);
        // Without `Vary` a shared cache stores every coding under one key.
        assert_eq!(
            revalidated.headers().get(VARY).expect("missing Vary"),
            "accept-encoding"
        );
    }

    #[tokio::test]
    async fn weak_etag_from_a_compressed_response_still_revalidates() {
        let dir = fixture().await;

        let compressed = router(&dir)
            .oneshot(
                get("gzip")
                    .body(Body::empty())
                    .expect("failed to build request"),
            )
            .await
            .expect("request failed");

        assert_eq!(compressed.status(), StatusCode::OK);
        let etag = etag_of(&compressed);
        assert!(
            etag.starts_with("W/"),
            "expected a weak validator, got {etag}"
        );

        let revalidated = router(&dir)
            .oneshot(
                get("gzip")
                    .header(IF_NONE_MATCH, etag.as_str())
                    .body(Body::empty())
                    .expect("failed to build request"),
            )
            .await
            .expect("request failed");

        // Weak comparison still matches the tag `ServeDir` derives from the file
        // metadata, so weakening does not cost a revalidation.
        assert_eq!(revalidated.status(), StatusCode::NOT_MODIFIED);
        assert_eq!(
            revalidated.headers().get(VARY).expect("missing Vary"),
            "accept-encoding"
        );
    }
}
