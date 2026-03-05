use tower_http::trace::{
    DefaultMakeSpan, DefaultOnRequest, DefaultOnResponse, HttpMakeClassifier, TraceLayer,
};
use tracing::Level;

pub(crate) fn trace_layer() -> TraceLayer<HttpMakeClassifier> {
    TraceLayer::new_for_http()
        .make_span_with(DefaultMakeSpan::new().level(Level::INFO))
        .on_request(DefaultOnRequest::new().level(Level::TRACE))
        .on_response(DefaultOnResponse::new().level(Level::INFO))
}
