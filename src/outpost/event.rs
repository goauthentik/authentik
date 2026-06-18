use std::{fmt::Display, sync::Arc};

use ak_common::{Arbiter, Tasks, VERSION, api, arbiter, authentik_build_hash};
use axum::http::{HeaderValue, header::AUTHORIZATION};
use eyre::{Result, eyre};
use futures::{SinkExt as _, StreamExt as _};
use nix::unistd::gethostname;
use serde::{Deserialize, Serialize};
use serde_repr::{Deserialize_repr, Serialize_repr};
use time::UtcDateTime;
use tokio::{
    signal::unix::SignalKind,
    time::{Duration, interval, sleep},
};
use tokio_tungstenite::tungstenite::{Message, client::IntoClientRequest as _};
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
        #[expect(
            clippy::unimplemented,
            reason = "this is only relevant for the RAC provider"
        )]
        EventKind::ProviderSpecific => unimplemented!(),
    }
    Ok(())
}

async fn watch_events_inner<O: Outpost>(
    arbiter: Arbiter,
    controller: Arc<OutpostController>,
    outpost: Arc<O>,
    attempt: u32,
) -> Result<()> {
    let server_config = api::ServerConfig::new()?;
    let ws_url = build_ws_url(
        server_config.host,
        &controller.outpost.load().pk.to_string(),
        &controller.instance_uuid.to_string(),
        attempt,
    )?;

    debug!(url = %ws_url, "connecting to websocket");
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

    let (ws_stream, _response) = tokio_tungstenite::connect_async(request).await?;
    let (mut ws_write, mut ws_read) = ws_stream.split();

    info!(
        outpost = %controller.outpost.load().pk,
        "connected to websocket"
    );
    controller.m_connection.set(1_u8);

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
            Ok(arbiter::Event::Signal(signal)) = events_rx.recv() => {
                if signal == SignalKind::user_defined1() {
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

async fn watch_events<O: Outpost>(
    arbiter: Arbiter,
    controller: Arc<OutpostController>,
    outpost: Arc<O>,
) -> Result<()> {
    const MAX_BACKOFF: Duration = Duration::from_mins(5);
    let mut backoff = Duration::from_secs(1);
    let mut attempt: u32 = 0;

    loop {
        tokio::select! {
            () = arbiter.shutdown() => break,
            res = watch_events_inner(
                arbiter.clone(),
                Arc::clone(&controller),
                Arc::clone(&outpost),
                attempt
            ) => {
                controller.m_connection.set(0_u8);
                match res {
                    Ok(()) => debug!("websocket disconnected cleanly"),
                    Err(err) => warn!(?err, attempt, "websocket error"),
                }

                info!(attempt, delay = backoff.as_secs(), "reconnecting websocket in {}s...", backoff.as_secs());

                tokio::select! {
                    () = arbiter.shutdown() => break,
                    () = sleep(backoff) => {}
                }

                backoff = (backoff * 2).min(MAX_BACKOFF);
                attempt += 1;
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
