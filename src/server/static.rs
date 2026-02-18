use crate::config::get_config;
use aws_lc_rs::digest;
use axum::{
    Router,
    extract::{Query, Request, State},
    http::{
        StatusCode,
        header::{self, CONTENT_SECURITY_POLICY},
    },
    middleware::{self, Next},
    response::Response,
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

    let token_header = match decode_header(&token_string) {
        Ok(header) => header,
        Err(_) => return false,
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
        .map(|b| format!("{:02x}", b))
        .collect::<String>();

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

    let claim_path = match claims.path {
        Some(path) => path,
        None => return false,
    };
    // Decode path before comparison so encoded URL segments cannot bypass path binding.
    let request_path = match percent_decode_str(request.uri().path()).decode_utf8() {
        Ok(path) => path,
        Err(_) => return false,
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
    if !is_storage_token_valid(config.usage, &get_config().await.secret_key, &request) {
        return Response::builder()
            .status(StatusCode::NOT_FOUND)
            .body("404 page not found\n".into())
            .unwrap();
    }

    let mut response = next.run(request).await;

    if config.set_csp_header {
        // Since media is user-controlled, better be safe
        response.headers_mut().insert(
            CONTENT_SECURITY_POLICY,
            "default-src 'none'; style-src 'unsafe-inline'; sandbox"
                .parse()
                .unwrap(),
        );
    }

    response
}

async fn static_header_middleware(request: Request, next: Next) -> Response {
    let mut response = next.run(request).await;

    response.headers_mut().insert(
        header::CACHE_CONTROL,
        "public, no-transform".parse().unwrap(),
    );
    response.headers_mut().insert(
        "X-authentik-version",
        env!("CARGO_PKG_VERSION").parse().unwrap(),
    );
    response
        .headers_mut()
        .insert(header::VARY, "X-authentik-version, Etag".parse().unwrap());

    // TODO: etag

    response
}

pub(crate) async fn build_router() -> Router {
    let config = get_config().await;

    let mut router = Router::new().layer(middleware::from_fn(static_header_middleware));

    let dist_fs = ServeDir::new("./web/dist/").append_index_html_on_directories(false);
    let static_fs = ServeDir::new("./web/authentik/").append_index_html_on_directories(false);

    router = router.nest_service("/static/dist/", dist_fs.clone());
    router = router.nest_service("/static/authentik/", static_fs.clone());

    router = router.nest_service("/if/flow/{flow_slug}/assets/", dist_fs.clone());
    router = router.nest_service("/if/admin/assets/", dist_fs.clone());
    router = router.nest_service("/if/user/assets/", dist_fs.clone());
    router = router.nest_service("/if/rac/{app_slug}/assets/", dist_fs.clone());

    let default_backend = &config.storage.backend;
    let media_backend = config
        .storage
        .media
        .clone()
        .unwrap_or_default()
        .backend
        .unwrap_or(default_backend.clone());
    let reports_backend = config
        .storage
        .reports
        .clone()
        .unwrap_or_default()
        .backend
        .unwrap_or(default_backend.clone());

    let default_path = &config.storage.file.path;

    if media_backend == "file" {
        let mut media_path = config
            .storage
            .media
            .clone()
            .unwrap_or_default()
            .file
            .unwrap_or_default()
            .path
            .unwrap_or(default_path.clone());
        media_path.push("media");

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
        let mut reports_path = config
            .storage
            .reports
            .clone()
            .unwrap_or_default()
            .file
            .unwrap_or_default()
            .path
            .unwrap_or(default_path.clone());
        reports_path.push("reports");

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
        any(|| async { include_str!("../../web/robots.txt") }),
    );
    router = router.route(
        "/.well-known/security.txt",
        any(|| async { include_str!("../../web/security.txt") }),
    );

    router = router.layer(middleware::from_fn(static_header_middleware));

    router = router.layer(CompressionLayer::new().compress_when(SizeAbove::new(32)));

    router
}
