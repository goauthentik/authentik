use authentik_config::get_config;
use axum::{
    Router,
    extract::Request,
    http::header,
    middleware::{self, Next},
    response::Response,
    routing::any,
};
use tower_http::{
    compression::{CompressionLayer, predicate::SizeAbove},
    services::fs::ServeDir,
};

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

        // TODO: handle perms
        let media_fs = ServeDir::new(media_path).append_index_html_on_directories(false);
        router = router.nest_service("/files/media/", media_fs);
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

        // TODO: handle perms
        let reports_fs = ServeDir::new(reports_path).append_index_html_on_directories(false);
        router = router.nest_service("/files/reports/", reports_fs);
    }

    router = router.route(
        "/robots.txt",
        any(|| async { include_str!("../../../web/robots.txt") }),
    );
    router = router.route(
        "/.well-known/security.txt",
        any(|| async { include_str!("../../../web/security.txt") }),
    );

    router = router.layer(middleware::from_fn(static_header_middleware));

    router = router.layer(CompressionLayer::new().compress_when(SizeAbove::new(32)));

    router
}
