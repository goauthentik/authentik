use std::collections::HashMap;
use std::sync::Arc;

use ak_axum::error::Result;
use ak_client::apis::events_api::events_events_create;
use ak_client::models::{EventActions, EventRequest};
use axum::{
    extract::{Request, State},
    http::HeaderMap,
    response::Response,
};
use eyre::{Result as EyreResult, eyre};
use serde_json::json;
use tracing::{instrument, warn};
use url::Url;

use crate::outpost::proxy::application::Application;

fn header_str<'a>(headers: &'a HeaderMap, name: &str) -> Option<&'a str> {
    headers.get(name)?.to_str().ok()
}

/// Build the forwarded URL from Traefik/Caddy `X-Forwarded-*` headers.
pub(super) fn traefik_forward_url(headers: &HeaderMap) -> EyreResult<Url> {
    let proto = header_str(headers, "x-forwarded-proto").unwrap_or_default();
    let host = header_str(headers, "x-forwarded-host").unwrap_or_default();
    let uri = header_str(headers, "x-forwarded-uri").unwrap_or_default();
    Ok(Url::parse(&format!("{proto}://{host}{uri}"))?)
}

/// Build the forwarded URL from nginx's `X-Original-URL` header.
pub(super) fn nginx_forward_url(headers: &HeaderMap) -> EyreResult<Url> {
    let original =
        header_str(headers, "x-original-url").ok_or_else(|| eyre!("no forward URL found"))?;
    Ok(Url::parse(original)?)
}

impl Application {
    /// Report a forward-auth misconfiguration as a configuration-error event.
    pub(super) async fn report_misconfiguration(&self, message: &str, url: &str) {
        let context = HashMap::from([
            ("message".to_owned(), json!(message)),
            ("provider".to_owned(), json!(self.provider.name)),
            ("outpost".to_owned(), json!(self.outpost_name)),
            ("url".to_owned(), json!(url)),
        ]);
        let event = EventRequest {
            context: Some(context),
            ..EventRequest::new(
                EventActions::ConfigurationError,
                "authentik.providers.proxy".to_owned(),
            )
        };
        if let Err(err) = events_events_create(&self.api_config, event).await {
            warn!(?err, "failed to report configuration error");
        }
    }
}

#[instrument(skip_all)]
pub(crate) async fn handle_caddy(
    State(_app): State<Arc<Application>>,
    _request: Request,
) -> Result<Response> {
    todo!()
}

#[instrument(skip_all)]
pub(crate) async fn handle_envoy(
    State(_app): State<Arc<Application>>,
    _request: Request,
) -> Result<Response> {
    todo!()
}

#[instrument(skip_all)]
pub(crate) async fn handle_nginx(
    State(_app): State<Arc<Application>>,
    _request: Request,
) -> Result<Response> {
    todo!()
}

#[instrument(skip_all)]
pub(crate) async fn handle_traefik(
    State(_app): State<Arc<Application>>,
    _request: Request,
) -> Result<Response> {
    todo!()
}

#[cfg(test)]
mod tests {
    use axum::http::{HeaderMap, HeaderValue};

    use super::{nginx_forward_url, traefik_forward_url};

    #[test]
    fn parses_traefik_forward_url() {
        let mut headers = HeaderMap::new();
        headers.insert("x-forwarded-proto", HeaderValue::from_static("https"));
        headers.insert(
            "x-forwarded-host",
            HeaderValue::from_static("app.example.com"),
        );
        headers.insert("x-forwarded-uri", HeaderValue::from_static("/foo?bar=1"));

        let url = traefik_forward_url(&headers).expect("forward url");
        assert_eq!(url.as_str(), "https://app.example.com/foo?bar=1");
    }

    #[test]
    fn traefik_without_headers_errors() {
        let _ = traefik_forward_url(&HeaderMap::new()).expect_err("missing headers should error");
    }

    #[test]
    fn parses_nginx_forward_url() {
        let mut headers = HeaderMap::new();
        headers.insert(
            "x-original-url",
            HeaderValue::from_static("https://app.example.com/app"),
        );

        let url = nginx_forward_url(&headers).expect("forward url");
        assert_eq!(url.as_str(), "https://app.example.com/app");
    }

    #[test]
    fn nginx_without_header_errors() {
        let _ = nginx_forward_url(&HeaderMap::new()).expect_err("missing header should error");
    }
}
