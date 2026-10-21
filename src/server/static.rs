use std::fmt::Write as _;

use aws_lc_rs::digest;
use axum::{
    Router,
    extract::{Query, Request, State},
    http::{
        HeaderValue, StatusCode,
        header::{CACHE_CONTROL, CONTENT_SECURITY_POLICY},
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
            header::{ACCEPT_ENCODING, CONTENT_ENCODING, CONTENT_LENGTH, CONTENT_RANGE, RANGE},
        },
    };
    use http_body_util::BodyExt as _;
    use tempfile::{TempDir, tempdir};
    use tokio::fs;
    use tower::ServiceExt as _;
    use tower_http::services::fs::ServeDir;

    use super::compression_layer;

    /// Enough bytes to clear the `SizeAbove` threshold, and compressible enough
    /// that gzip is a visible win.
    const BODY: &[u8] = &[b'a'; 4096];

    /// Mirrors how [`build_router`] serves `/static/dist/`: a `ServeDir` under
    /// the shared compression layer.
    fn router(dir: &TempDir) -> Router {
        Router::new()
            .nest_service(
                "/static/dist/",
                ServeDir::new(dir.path()).append_index_html_on_directories(false),
            )
            .layer(compression_layer())
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
}
