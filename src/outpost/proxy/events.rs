//! Reporting events back to authentik.

use std::{collections::HashMap, net::IpAddr};

use ak_client::{
    apis::events_api::events_events_create,
    models::{EventActions, EventRequest},
};
use axum::http::HeaderMap;
use serde_json::{Map, Value, json};
use tracing::{error, warn};

use crate::outpost::proxy::application::Application;

impl Application {
    /// Report a misconfiguration as a configuration-error event (best-effort).
    pub(super) async fn report_misconfiguration(
        &self,
        message: &str,
        url: &str,
        headers: &HeaderMap,
        client_ip: IpAddr,
    ) {
        error!(
            provider = %self.provider.name,
            url = %url,
            client_ip = %client_ip,
            "configuration error: {message}"
        );

        // First value of each request header, attached to the event for debugging.
        let request_headers: Map<String, Value> = headers
            .keys()
            .map(|name| {
                let value = headers
                    .get(name)
                    .and_then(|value| value.to_str().ok())
                    .unwrap_or_default();
                (name.as_str().to_owned(), Value::from(value))
            })
            .collect();

        let context = HashMap::from([
            ("message".to_owned(), json!(message)),
            ("provider".to_owned(), json!(self.provider.name)),
            ("outpost".to_owned(), json!(self.outpost_name)),
            ("url".to_owned(), json!(url)),
            ("headers".to_owned(), Value::Object(request_headers)),
        ]);
        let event = EventRequest {
            context: Some(context),
            client_ip: Some(Some(client_ip.to_string())),
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
