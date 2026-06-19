//! Reporting events back to authentik.

use std::collections::HashMap;

use ak_client::{
    apis::events_api::events_events_create,
    models::{EventActions, EventRequest},
};
use serde_json::json;
use tracing::warn;

use crate::outpost::proxy::application::Application;

impl Application {
    /// Report a misconfiguration as a configuration-error event (best-effort).
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
