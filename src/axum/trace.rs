use std::time::Duration;

use axum::http::Request;
use hyper::Response;
use tower_http::trace::{
    DefaultOnResponse, HttpMakeClassifier, MakeSpan, OnRequest, OnResponse, TraceLayer,
};
use tracing::{Level, Span};

use crate::{axum::extract::client_ip::ClientIp, config};

#[derive(Clone)]
pub(crate) struct CustomOnRequest;

impl<B> OnRequest<B> for CustomOnRequest {
    fn on_request(&mut self, request: &Request<B>, _span: &Span) {
        tracing::trace!(event = %request.uri(), "request");
    }
}

#[derive(Clone)]
pub(crate) struct CustomMakeSpan;

impl<B> MakeSpan<B> for CustomMakeSpan {
    fn make_span(&mut self, request: &Request<B>) -> Span {
        let config = config::get();
        let remote = request
            .extensions()
            .get::<ClientIp>()
            .expect("ClientIp missing. Did you add the middleware?")
            .0;
        tracing::info_span!(
            "request",
            event = %request.uri(),
            remote = %remote,
            method = %request.method(),
            uri = %request.uri(),
            version = ?request.version(),
            headers = ?request.headers().iter().filter(|(name, _)| {
                for header in config.log.http_headers.iter() {
                    if header.eq_ignore_ascii_case(name.as_str()) {
                        return true;
                    }
                }
                false
            }).map(|(name, value)| (name.to_string().to_lowercase().replace("-", "_"), value))
            .collect::<Vec<_>>()
        )
    }
}

pub(crate) fn trace_layer() -> TraceLayer<HttpMakeClassifier, CustomMakeSpan, CustomOnRequest> {
    TraceLayer::new_for_http()
        .on_request(CustomOnRequest {})
        .on_response(DefaultOnResponse::new().level(Level::INFO))
        .make_span_with(CustomMakeSpan {})
}
