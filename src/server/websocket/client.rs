//! `/ws/client/`: notifications for the browser, replacing
//! `authentik.events.consumer.ClientConsumer`.
//!
//! Python still decides who may connect and still sends the notifications, see
//! `NotificationTransport.send_local` in `authentik/events/models.py`.

use std::{sync::Arc, time::Duration};

use ak_axum::extract::client_ip::ClientIp;
use axum::{
    extract::{
        OriginalUri, State,
        ws::{CloseFrame, Message, WebSocket, WebSocketUpgrade, close_code},
    },
    http::{HeaderMap, StatusCode},
    response::{IntoResponse as _, Response},
};
use serde_json::{Map, Value};
use tokio::{
    sync::mpsc,
    time::{Instant, MissedTickBehavior, interval_at, timeout},
};
use tracing::{debug, warn};

use super::{
    METRIC_CONNECTIONS, WebsocketState,
    contract::Route,
    layer::{Delivery, Subscription},
};
use crate::server::GUNICORN_READY;

/// How often we ping an idle browser to notice connections that died without closing.
const PING_INTERVAL: Duration = Duration::from_secs(30);
/// A browser that hasn't answered for this long is gone.
const IDLE_TIMEOUT: Duration = Duration::from_secs(75);
/// How long a browser may take to accept a message before we give up on it.
const SEND_TIMEOUT: Duration = Duration::from_secs(10);
/// Group memberships expire after a day, so connections refresh them well before then.
/// `ClientConsumer` never does, so its connections stop receiving notifications after a day.
const GROUP_REFRESH_INTERVAL: Duration = Duration::from_hours(1);
/// The browser only ever sends pongs and close frames.
const MAX_MESSAGE_SIZE: usize = 4 * 1024;

pub(super) async fn handler(
    State(state): State<Arc<WebsocketState>>,
    ClientIp(client_ip): ClientIp,
    OriginalUri(uri): OriginalUri,
    headers: HeaderMap,
    upgrade: WebSocketUpgrade,
) -> Response {
    if !GUNICORN_READY.load(std::sync::atomic::Ordering::Relaxed) {
        return StatusCode::SERVICE_UNAVAILABLE.into_response();
    }

    let authorization = match state
        .contract
        .authorize(Route::Client, uri.path(), &headers, client_ip)
        .await
    {
        Ok(authorization) => authorization,
        Err(err) => {
            warn!(?err, "failed to authorize WebSocket connection");
            return StatusCode::SERVICE_UNAVAILABLE.into_response();
        }
    };
    // Channels answers a denied handshake with a 403, which the relay passes on.
    if !authorization.accept {
        return StatusCode::FORBIDDEN.into_response();
    }

    // Joining before upgrading means a failure is an HTTP error instead of a socket that
    // never receives anything, and nothing sent while upgrading is missed.
    let (subscription, deliveries) =
        match Subscription::join(&state.layer, authorization.groups).await {
            Ok(joined) => joined,
            Err(err) => {
                warn!(?err, "failed to join channel layer groups");
                return StatusCode::SERVICE_UNAVAILABLE.into_response();
            }
        };

    upgrade
        .max_message_size(MAX_MESSAGE_SIZE)
        .on_failed_upgrade(|err| debug!(?err, "WebSocket upgrade failed"))
        // When the upgrade fails, the closure is dropped and the subscription with it.
        .on_upgrade(move |socket| serve(socket, state, subscription, deliveries))
}

async fn serve(
    mut socket: WebSocket,
    state: Arc<WebsocketState>,
    subscription: Subscription,
    mut deliveries: mpsc::Receiver<Delivery>,
) {
    let gauge = metrics::gauge!(METRIC_CONNECTIONS, "route" => "client");
    gauge.increment(1_u32);

    let mut ping = interval_at(Instant::now() + PING_INTERVAL, PING_INTERVAL);
    ping.set_missed_tick_behavior(MissedTickBehavior::Delay);
    let mut refresh = interval_at(
        Instant::now() + GROUP_REFRESH_INTERVAL,
        GROUP_REFRESH_INTERVAL,
    );
    let mut last_seen = Instant::now();

    let close = loop {
        tokio::select! {
            delivery = deliveries.recv() => {
                let Some(delivery) = delivery else {
                    break None;
                };
                let message = match state.layer.claim(delivery).await {
                    Ok(Some(message)) => message,
                    Ok(None) => continue,
                    Err(err) => {
                        warn!(?err, "failed to claim channel layer message");
                        continue;
                    }
                };
                let Some(text) = notification_text(message) else {
                    continue;
                };
                if !send(&mut socket, Message::Text(text.into())).await {
                    break None;
                }
            },
            incoming = socket.recv() => match incoming {
                Some(Ok(Message::Close(_)) | Err(_)) | None => break None,
                // Like `ClientConsumer`, we ignore anything the browser sends.
                Some(Ok(_)) => last_seen = Instant::now(),
            },
            _ = ping.tick() => {
                if last_seen.elapsed() > IDLE_TIMEOUT {
                    debug!("browser stopped answering, closing WebSocket connection");
                    break None;
                }
                if !send(&mut socket, Message::Ping(Vec::new().into())).await {
                    break None;
                }
            },
            _ = refresh.tick() => {
                if let Err(err) = subscription.refresh().await {
                    warn!(?err, "failed to refresh channel layer groups");
                }
            },
            () = state.arbiter.shutdown() => break Some(CloseFrame {
                code: close_code::RESTART,
                reason: "server restarting".into(),
            }),
        }
    };

    if let Some(frame) = close {
        let _ = send(&mut socket, Message::Close(Some(frame))).await;
    }
    gauge.decrement(1_u32);
    subscription.leave().await;
}

/// Sends a message, giving up on a browser that doesn't take it in time.
async fn send(socket: &mut WebSocket, message: Message) -> bool {
    match timeout(SEND_TIMEOUT, socket.send(message)).await {
        Ok(Ok(())) => true,
        Ok(Err(err)) => {
            debug!(?err, "failed to send WebSocket message");
            false
        }
        Err(_) => {
            debug!("browser is not reading, closing WebSocket connection");
            false
        }
    }
}

/// Turns a channel layer message into what `ClientConsumer` sends for it.
fn notification_text(message: Map<String, Value>) -> Option<String> {
    match message.get("type").and_then(Value::as_str) {
        // `ClientConsumer.event_notification`: {"message_type": "notification.new", **event}
        Some("event.notification") => {
            let mut text = Map::with_capacity(message.len() + 1);
            text.insert(
                "message_type".to_owned(),
                Value::String("notification.new".to_owned()),
            );
            text.extend(message);
            serde_json::to_string(&text).ok()
        }
        other => {
            debug!(?other, "ignoring channel layer message without a handler");
            None
        }
    }
}

#[cfg(test)]
mod tests {
    use serde_json::json;

    use super::*;
    use crate::server::websocket::codec::{self, tests::PYTHON_NOTIFICATION};

    #[test]
    fn notification_matches_client_consumer() {
        let message = codec::decode(PYTHON_NOTIFICATION).expect("failed to decode");
        let text = notification_text(message).expect("expected a notification");
        let value: Value = serde_json::from_str(&text).expect("invalid JSON");
        assert_eq!(value["message_type"], "notification.new");
        assert_eq!(value["type"], "event.notification");
        assert_eq!(value["id"], "5ba8d8bc-5d36-4a17-9bba-e1b8c3d6a0b4");
        assert_eq!(value["data"]["body"], "Ünïcödé body");
    }

    #[test]
    fn other_messages_are_ignored() {
        let Value::Object(message) = json!({"type": "event.something_else"}) else {
            unreachable!();
        };
        assert_eq!(notification_text(message), None);
    }
}
