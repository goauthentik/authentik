use std::{
    fmt::Display,
    sync::{Arc, OnceLock},
    time::Instant,
};

use ak_common::{Arbiter, Tasks, VERSION, api, arbiter, authentik_build_hash, config, tls};
use axum::http::{HeaderValue, header::AUTHORIZATION};
use eyre::{Result, eyre};
use futures::{Sink, SinkExt as _, Stream, StreamExt as _};
use nix::unistd::gethostname;
use serde::{Deserialize, Serialize};
use serde_repr::{Deserialize_repr, Serialize_repr};
use time::UtcDateTime;
use tokio::{
    net::UnixStream,
    signal::unix::SignalKind,
    time::{Duration, interval, sleep},
};
use tokio_tungstenite::{
    Connector,
    tungstenite::{Error as WsError, Message, client::IntoClientRequest as _},
};
use tracing::{debug, info, instrument, trace, warn};
use url::Url;

use crate::outpost::{Outpost, OutpostController};

#[derive(Serialize_repr, Deserialize_repr, PartialEq, Debug, Clone, Copy, Eq)]
#[repr(u8)]
enum EventKind {
    /// Code used to acknowledge a previous message.
    Ack = 0,
    /// Code used to send a healthcheck keepalive.
    Hello = 1,
    /// Code received to trigger a config update.
    TriggerUpdate = 2,
    /// Code received to trigger some provider specific function.
    ProviderSpecific = 3,
    /// Code received to identify the end of a session.
    SessionEnd = 4,
}

impl Display for EventKind {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Ack => write!(f, "Ack"),
            Self::Hello => write!(f, "Hello"),
            Self::TriggerUpdate => write!(f, "TriggerUpdate"),
            Self::ProviderSpecific => write!(f, "ProviderSpecific"),
            Self::SessionEnd => write!(f, "SessionEnd"),
        }
    }
}

#[derive(Serialize, Deserialize)]
struct Event {
    instruction: EventKind,
    args: serde_json::Value,
}

#[derive(Debug, Deserialize)]
pub(crate) struct EventSessionEnd {
    pub(crate) session_id: String,
}

fn build_ws_url(mut url: Url, outpost_pk: &str, instance_uuid: &str, attempt: u32) -> Result<Url> {
    let ws_scheme = match url.scheme() {
        "https" => "wss",
        "http" => "ws",
        other => return Err(eyre!("Unsupported scheme for WebSocket URL: {other}")),
    };

    url.set_scheme(ws_scheme)
        .map_err(|()| eyre!("Failed to set URL scheme to {ws_scheme}"))?;
    url.set_path(&format!("{}ws/outpost/{outpost_pk}/", url.path()));
    url.query_pairs_mut()
        .append_pair("instance_uuid", instance_uuid)
        .append_pair("attempt", &attempt.to_string());

    Ok(url)
}

fn hello_args(instance_uuid: &str) -> serde_json::Value {
    let raw_hostname = gethostname().unwrap_or_default();
    let hostname = raw_hostname.to_string_lossy();

    serde_json::json!({
        "version": VERSION,
        "buildHash": authentik_build_hash(None),
        "uuid": instance_uuid,
        // TODO: rust version and AWS-LC versions
        "hostname": hostname,
    })
}

#[instrument(skip_all)]
async fn handle_event<O: Outpost>(
    controller: Arc<OutpostController>,
    outpost: Arc<O>,
    event: Event,
    reload_offset: Option<Duration>,
) -> Result<()> {
    match event.instruction {
        EventKind::Ack | EventKind::Hello => {}
        EventKind::TriggerUpdate => {
            info!("received update trigger, refreshing outpost");
            if let Some(reload_offset) = reload_offset {
                sleep(reload_offset).await;
            }
            controller.refresh().await?;
            debug!("outpost controller has been refreshed");
            outpost.refresh().await?;
            debug!("outpost has been refreshed");
            #[expect(
                clippy::as_conversions,
                clippy::cast_precision_loss,
                reason = "This is fine, we'll never get big values here."
            )]
            controller
                .m_last_update
                .set(UtcDateTime::now().unix_timestamp() as f64);
        }
        EventKind::SessionEnd => {
            let event: EventSessionEnd = serde_json::from_value(event.args)?;
            outpost.end_session(event).await?;
        }
        EventKind::ProviderSpecific => {
            debug!("received provider specific event. ignoring.");
        }
    }
    Ok(())
}

async fn watch_events_inner<O: Outpost>(
    arbiter: Arbiter,
    controller: Arc<OutpostController>,
    outpost: Arc<O>,
    attempt: u32,
    connected_at: &OnceLock<Instant>,
) -> Result<()> {
    type WsWriter = Box<dyn Sink<Message, Error = WsError> + Unpin + Send>;
    type WsReader = Box<dyn Stream<Item = Result<Message, WsError>> + Unpin + Send>;

    info!("refreshing outpost forcefully");
    if let Err(err) = handle_event(
        Arc::clone(&controller),
        Arc::clone(&outpost),
        Event {
            instruction: EventKind::TriggerUpdate,
            args: serde_json::Value::Null,
        },
        None,
    )
    .await
    {
        warn!(?err, "failed to refresh");
    }

    let (host, insecure) = if controller.is_embedded() {
        (
            Url::parse(&format!("http://localhost{}", config::get().web.path))?,
            false,
        )
    } else {
        let server_config = api::ServerConfig::new()?;
        (server_config.host, server_config.insecure)
    };

    let ws_url = build_ws_url(
        host,
        &controller.outpost.load().pk.to_string(),
        &controller.instance_uuid.to_string(),
        attempt,
    )?;

    debug!(url = %ws_url, insecure, "connecting to websocket");
    let mut request = ws_url.into_client_request()?;
    let token = controller
        .api_config
        .bearer_access_token
        .as_deref()
        .unwrap_or("");
    request.headers_mut().insert(
        AUTHORIZATION,
        HeaderValue::from_str(&format!("Bearer {token}"))?,
    );

    // Embedded outposts run inside the core server and reach it over its unix socket,
    // which only exists when built with the `core` feature.
    let embedded_stream = if controller.is_embedded() {
        #[cfg(feature = "core")]
        {
            Some(UnixStream::connect(crate::server::socket_path()).await?)
        }
        #[cfg(not(feature = "core"))]
        {
            None::<UnixStream>
        }
    } else {
        None
    };

    let (mut ws_write, mut ws_read): (WsWriter, WsReader) = if let Some(stream) = embedded_stream {
        let (ws_stream, _response) = tokio_tungstenite::client_async(request, stream).await?;
        let (write, read) = ws_stream.split();
        (Box::new(write), Box::new(read))
    } else {
        let connector =
            insecure.then(|| Connector::Rustls(Arc::new(tls::client::insecure_config())));
        let (ws_stream, _response) =
            tokio_tungstenite::connect_async_tls_with_config(request, None, false, connector)
                .await?;
        let (write, read) = ws_stream.split();
        (Box::new(write), Box::new(read))
    };

    info!(
        outpost = %controller.outpost.load().pk,
        "connected to websocket"
    );
    controller.m_connection.set(1_u8);
    let _ = connected_at.set(Instant::now());

    let get_refresh_interval = || {
        let mut interval = controller.outpost.load().refresh_interval_s;
        // Ensure timer interval is not negative or 0.
        // If it is, we default to 5 minutes.
        if interval <= 0_i32 {
            interval = 60_i32 * 5_i32;
        }
        // Clamp interval to be at least 30 seconds.
        if interval < 30_i32 {
            interval = 30_i32;
        }
        // infallible because we bound it to be positive above
        Duration::from_secs(interval.try_into().expect("infallible"))
    };
    let mut refresh_interval = interval(get_refresh_interval());
    let mut heartbeat_interval = interval(Duration::from_secs(10));

    let mut events_rx = arbiter.events_subscribe();

    loop {
        tokio::select! {
            _ = refresh_interval.tick() => {
                info!("refreshing outpost on interval");
                if let Err(err) = handle_event(
                    Arc::clone(&controller),
                    Arc::clone(&outpost),
                    Event {
                        instruction: EventKind::TriggerUpdate,
                        args: serde_json::Value::Null
                    },
                    None,
                ).await {
                    warn!(?err, "failed to refresh");
                }
                refresh_interval = interval(get_refresh_interval());
                // Since we re-create the interval, we need to make it tick instantly to avoid
                // ending up in a never-ending tick-loop.
                refresh_interval.tick().await;
            },
            _ = heartbeat_interval.tick() => {
                let ping = Event {
                    instruction: EventKind::Hello,
                    args: hello_args(&controller.instance_uuid.to_string()),
                };
                ws_write.send(Message::text(serde_json::to_string(&ping)?)).await?;
                trace!("sent websocket hello (heartbeat)");
            },
            event = events_rx.recv() => {
                if let Ok(arbiter::Event::Signal(signal)) = event && signal == SignalKind::user_defined1() {
                    info!("refreshing outpost on signal");
                    if let Err(err) = handle_event(
                        Arc::clone(&controller),
                        Arc::clone(&outpost),
                        Event {
                            instruction: EventKind::TriggerUpdate,
                            args: serde_json::Value::Null
                        },
                        None,
                    ).await {
                        warn!(?err, "failed to refresh");
                    }
                }
            },
            msg = ws_read.next() => {
                let Some(msg) = msg else {
                    break;
                };
                let msg = msg?;
                match msg {
                    Message::Text(text) => {
                        let Ok(event): Result<Event, _> = serde_json::from_str(&text) else {
                            warn!(data = text.as_str(), "failed to parse event");
                            continue;
                        };
                        trace!(event = %event.instruction, "received websocket event");
                        if let Err(err) = handle_event(
                            Arc::clone(&controller),
                            Arc::clone(&outpost),
                            event,
                            Some(controller.reload_offset),
                        ).await {
                            warn!(?err, "failed to handle event");
                        }
                    },
                    Message::Ping(data) => {
                        ws_write.send(Message::Pong(data)).await?;
                    },
                    Message::Close(_) => {
                        break;
                    },
                    _ => {},
                }
            },
            () = arbiter.shutdown() => break,
        }
    }

    Ok(())
}

/// Reconnect delay and attempt counter of the event watcher.
struct Reconnect {
    delay: Duration,
    attempt: u32,
}

impl Reconnect {
    const INITIAL_DELAY: Duration = Duration::from_secs(1);
    const MAX_DELAY: Duration = Duration::from_mins(5);
    /// A session must stay connected at least this long to count as healthy.
    const STABLE_SESSION: Duration = Duration::from_mins(1);

    const fn new() -> Self {
        Self {
            delay: Self::INITIAL_DELAY,
            attempt: 0,
        }
    }

    /// Start over after a healthy session. Connection failures and short-lived sessions keep
    /// the exponential backoff, so a server that accepts and immediately drops is not hammered.
    fn session_ended(&mut self, connected_for: Option<Duration>) {
        if connected_for.is_some_and(|duration| duration >= Self::STABLE_SESSION) {
            *self = Self::new();
        }
    }

    /// Grow the delay after waiting for it.
    fn waited(&mut self) {
        self.delay = (self.delay * 2).min(Self::MAX_DELAY);
        self.attempt += 1;
    }
}

async fn watch_events<O: Outpost>(
    arbiter: Arbiter,
    controller: Arc<OutpostController>,
    outpost: Arc<O>,
) -> Result<()> {
    let mut reconnect = Reconnect::new();

    loop {
        let connected_at = OnceLock::new();
        tokio::select! {
            () = arbiter.shutdown() => break,
            res = watch_events_inner(
                arbiter.clone(),
                Arc::clone(&controller),
                Arc::clone(&outpost),
                reconnect.attempt,
                &connected_at,
            ) => {
                controller.m_connection.set(0_u8);
                reconnect.session_ended(connected_at.get().map(Instant::elapsed));
                let Reconnect { delay, attempt } = reconnect;
                match res {
                    Ok(()) => debug!("websocket disconnected cleanly"),
                    Err(err) => warn!(?err, attempt, "websocket error"),
                }

                info!(attempt, delay = delay.as_secs(), "reconnecting websocket in {}s...", delay.as_secs());

                tokio::select! {
                    () = arbiter.shutdown() => break,
                    () = sleep(delay) => {}
                }

                reconnect.waited();
            }
        }
    }

    info!("stopping event watcher");

    Ok(())
}

pub(crate) fn start<O: Outpost + 'static>(
    tasks: &mut Tasks,
    controller: Arc<OutpostController>,
    outpost: Arc<O>,
) -> Result<()> {
    let arbiter = tasks.arbiter();
    tasks
        .build_task()
        .name(&format!("{}::watch_events", module_path!()))
        .spawn(watch_events(arbiter, controller, outpost))?;

    Ok(())
}

#[cfg(test)]
mod tests {
    use tokio::time::Duration;

    use super::Reconnect;

    fn saturated() -> Reconnect {
        let mut reconnect = Reconnect::new();
        for _ in 0_u8..20_u8 {
            reconnect.waited();
        }
        reconnect
    }

    #[test]
    fn delay_grows_up_to_the_maximum() {
        let mut reconnect = Reconnect::new();
        let mut delays = Vec::new();
        for _ in 0_u8..12_u8 {
            delays.push(reconnect.delay.as_secs());
            reconnect.waited();
        }
        assert_eq!(delays, [1, 2, 4, 8, 16, 32, 64, 128, 256, 300, 300, 300]);
        assert_eq!(reconnect.attempt, 12);
    }

    #[test]
    fn stable_session_resets_backoff() {
        let mut reconnect = saturated();
        assert_eq!(reconnect.delay, Reconnect::MAX_DELAY);

        reconnect.session_ended(Some(Reconnect::STABLE_SESSION));

        assert_eq!(reconnect.delay, Reconnect::INITIAL_DELAY);
        assert_eq!(reconnect.attempt, 0);
    }

    #[test]
    fn failed_connection_keeps_backoff() {
        let mut reconnect = saturated();
        let attempt = reconnect.attempt;

        reconnect.session_ended(None);

        assert_eq!(reconnect.delay, Reconnect::MAX_DELAY);
        assert_eq!(reconnect.attempt, attempt);
    }

    #[test]
    fn short_session_keeps_backoff() {
        let mut reconnect = saturated();
        let attempt = reconnect.attempt;

        reconnect.session_ended(Some(Duration::from_secs(59)));

        assert_eq!(reconnect.delay, Reconnect::MAX_DELAY);
        assert_eq!(reconnect.attempt, attempt);
    }
}
