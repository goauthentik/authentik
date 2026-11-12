//! The Rust side of the PostgreSQL channel layer.
//!
//! Python keeps producing messages, for example with `group_send_blocking`, see
//! `packages/django-channels-postgres/django_channels_postgres/layer.py`. This module receives
//! them for the WebSocket connections the Rust server serves itself:
//!
//! - it joins and leaves groups through the same `groupchannel` table,
//! - it `LISTEN`s on the same `NOTIFY` channel the message table's trigger notifies,
//! - it claims a message by deleting its row, the same way Python consumers do.
//!
//! Python and Rust consumers share the tables, so they work side by side, including across
//! replicas running different versions during a rolling upgrade.

use std::{
    collections::HashMap,
    sync::{Arc, PoisonError, RwLock},
    time::{Duration, SystemTime, UNIX_EPOCH},
};

use ak_common::Arbiter;
use eyre::{Result, eyre};
use serde_json::{Map, Value};
use sqlx::{
    PgPool,
    postgres::{PgListener, PgPoolOptions},
};
use tokio::{
    sync::{
        mpsc::{self, error::TrySendError},
        watch,
    },
    time::sleep,
};
use tracing::{debug, info, trace, warn};
use uuid::Uuid;

use super::codec;

/// The layer's `prefix`, which is the default since `CHANNEL_LAYERS` doesn't set one.
const PREFIX: &str = "asgi";
/// `NOTIFY_CHANNEL` in `django_channels_postgres/models.py`.
const NOTIFY_CHANNEL: &str = "channels_messages";
/// How many messages may wait for a connection before new ones are dropped.
const QUEUE_CAPACITY: usize = 64;
/// How long to wait before listening again after losing the connection.
const RECONNECT_DELAY: Duration = Duration::from_secs(1);

pub(super) const METRIC_DROPPED: &str = "authentik_main_websocket_messages_dropped";

/// A message waiting for a connection.
#[derive(Debug)]
pub(super) enum Delivery {
    /// Announced by `NOTIFY`, the message still has to be claimed.
    Notified(Uuid),
    /// Already claimed while catching up after a reconnect.
    Claimed(Vec<u8>),
}

#[derive(Debug)]
pub(super) struct Layer {
    pool: PgPool,
    channels: RwLock<HashMap<String, mpsc::Sender<Delivery>>>,
    /// Whether we're listening for messages, after catching up on missed ones.
    listening: watch::Sender<bool>,
}

impl Layer {
    pub(super) fn new(pool: PgPool) -> Self {
        Self {
            pool,
            channels: RwLock::new(HashMap::new()),
            listening: watch::Sender::new(false),
        }
    }

    /// Resolves once we're listening for messages.
    #[cfg(test)]
    pub(super) async fn wait_listening(&self) {
        self.listening
            .subscribe()
            .wait_for(|listening| *listening)
            .await
            .expect("the layer was dropped");
    }

    /// Creates a channel for one connection, named like the ones `new_channel` creates in Python.
    fn new_channel(&self) -> (String, mpsc::Receiver<Delivery>) {
        let channel = format!("{PREFIX}.rust.{}", Uuid::new_v4().simple());
        let (tx, rx) = mpsc::channel(QUEUE_CAPACITY);
        self.channels
            .write()
            .unwrap_or_else(PoisonError::into_inner)
            .insert(channel.clone(), tx);
        (channel, rx)
    }

    fn remove_channel(&self, channel: &str) {
        self.channels
            .write()
            .unwrap_or_else(PoisonError::into_inner)
            .remove(channel);
    }

    fn group_key(group: &str) -> String {
        format!("{PREFIX}.group.{group}")
    }

    /// Adds `channel` to `group` or refreshes its expiry, like `group_add`.
    async fn group_add(&self, group: &str, channel: &str) -> Result<()> {
        sqlx::query(
            "WITH updated AS (
                UPDATE django_channels_postgres_groupchannel
                SET expires = now() + interval '1 day'
                WHERE group_key = $1 AND channel = $2
                RETURNING id
            )
            INSERT INTO django_channels_postgres_groupchannel (id, group_key, channel, expires)
            SELECT $3, $1, $2, now() + interval '1 day'
            WHERE NOT EXISTS (SELECT FROM updated)",
        )
        .bind(Self::group_key(group))
        .bind(channel)
        .bind(Uuid::new_v4())
        .execute(&self.pool)
        .await?;
        Ok(())
    }

    /// Removes `channel` from `group`, like `group_discard`.
    async fn group_discard(&self, group: &str, channel: &str) -> Result<()> {
        sqlx::query(
            "DELETE FROM django_channels_postgres_groupchannel
            WHERE group_key = $1 AND channel = $2",
        )
        .bind(Self::group_key(group))
        .bind(channel)
        .execute(&self.pool)
        .await?;
        Ok(())
    }

    /// Claims and decodes a message.
    ///
    /// Returns `None` when the message is gone: it expired and was cleaned up, or it was
    /// already claimed while catching up after a reconnect. Deleting the row is what claims a
    /// message, so each one is delivered once even when it was both caught up on and announced.
    pub(super) async fn claim(&self, delivery: Delivery) -> Result<Option<Map<String, Value>>> {
        let message = match delivery {
            Delivery::Claimed(message) => message,
            Delivery::Notified(id) => {
                let row: Option<(Vec<u8>,)> = sqlx::query_as(
                    "DELETE FROM django_channels_postgres_message WHERE id = $1 RETURNING message",
                )
                .bind(id)
                .fetch_optional(&self.pool)
                .await?;
                let Some((message,)) = row else {
                    return Ok(None);
                };
                message
            }
        };
        codec::decode(&message).map(Some)
    }

    /// Hands a message to the connection its channel belongs to, without waiting.
    ///
    /// The listener must never wait for a connection: PostgreSQL queues notifications for
    /// every listener, so a stalled one grows the server-wide queue. A connection that can't
    /// keep up loses messages instead.
    fn deliver(&self, channel: &str, delivery: Delivery) {
        let Some(tx) = self
            .channels
            .read()
            .unwrap_or_else(PoisonError::into_inner)
            .get(channel)
            .cloned()
        else {
            return;
        };
        match tx.try_send(delivery) {
            // A closed connection is going away and has nothing left to receive.
            Ok(()) | Err(TrySendError::Closed(_)) => {}
            Err(TrySendError::Full(_)) => {
                metrics::counter!(METRIC_DROPPED).increment(1);
                warn!(channel, "connection is not keeping up, dropping message");
            }
        }
    }

    /// Handles a notification from the message table's trigger.
    fn dispatch(&self, payload: &str) {
        let Some(notification) = Notification::parse(payload) else {
            debug!(payload, "ignoring malformed channel layer notification");
            return;
        };
        if notification.is_expired() {
            return;
        }
        self.deliver(notification.channel, Delivery::Notified(notification.id));
    }

    /// Claims messages for our channels that arrived while we weren't listening.
    async fn catch_up(&self) -> Result<()> {
        let channels: Vec<String> = self
            .channels
            .read()
            .unwrap_or_else(PoisonError::into_inner)
            .keys()
            .cloned()
            .collect();
        if channels.is_empty() {
            return Ok(());
        }
        let rows: Vec<(String, Vec<u8>)> = sqlx::query_as(
            "WITH claimed AS (
                DELETE FROM django_channels_postgres_message
                WHERE channel = ANY($1) AND expires >= now()
                RETURNING id, channel, message, expires
            )
            SELECT channel, message FROM claimed ORDER BY expires, id",
        )
        .bind(channels)
        .fetch_all(&self.pool)
        .await?;
        debug!(count = rows.len(), "caught up on channel layer messages");
        for (channel, message) in rows {
            self.deliver(&channel, Delivery::Claimed(message));
        }
        Ok(())
    }

    async fn listen(&self) -> Result<()> {
        // A dedicated connection: a pooled one would go back to the pool still listening.
        // TODO: use the `postgresql.direct` endpoint once the Rust config knows about it, like
        // the Python layer does. `LISTEN` doesn't work through a transaction-mode pooler.
        let pool = PgPoolOptions::new()
            .max_connections(1)
            .connect_lazy_with((*self.pool.connect_options()).clone());
        let mut listener = PgListener::connect_with(&pool).await?;
        listener.listen(NOTIFY_CHANNEL).await?;
        info!("listening for channel layer messages");
        // Only once we're listening, so nothing sent in between is missed. A message both
        // caught up on and announced is claimed once, see `claim`.
        self.catch_up().await?;
        self.listening.send_replace(true);
        loop {
            let Some(notification) = listener.try_recv().await? else {
                return Err(eyre!("lost the connection to PostgreSQL"));
            };
            trace!(payload = notification.payload(), "received notification");
            self.dispatch(notification.payload());
        }
    }

    /// Receives messages until the server shuts down.
    pub(super) async fn run(self: Arc<Self>, arbiter: Arbiter) -> Result<()> {
        loop {
            tokio::select! {
                res = self.listen() => {
                    self.listening.send_replace(false);
                    if let Err(err) = res {
                        warn!(?err, "channel layer listener failed, reconnecting");
                    }
                },
                () = arbiter.shutdown() => return Ok(()),
            }
            tokio::select! {
                () = sleep(RECONNECT_DELAY) => {},
                () = arbiter.shutdown() => return Ok(()),
            }
        }
    }
}

/// A notification from the message table's trigger, see `notify_new_channels_message` in
/// `django_channels_postgres/models.py`: `id:channel:expires`, followed by `:message` when the
/// message is small enough to fit.
#[derive(Debug, PartialEq)]
struct Notification<'a> {
    id: Uuid,
    channel: &'a str,
    expires: f64,
}

impl<'a> Notification<'a> {
    fn parse(payload: &'a str) -> Option<Self> {
        // We ignore an inlined message and claim it from the table instead, so a message is
        // delivered once even when catching up also claimed it.
        let mut parts = payload.splitn(4, ':');
        let id = parts.next()?.parse().ok()?;
        let channel = parts.next()?;
        let expires = parts.next()?.parse().ok()?;
        Some(Self {
            id,
            channel,
            expires,
        })
    }

    fn is_expired(&self) -> bool {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map_or(0.0_f64, |now| now.as_secs_f64());
        self.expires < now
    }
}

/// A connection's channel and the groups it joined. Leaves them when dropped.
#[derive(Debug)]
pub(super) struct Subscription {
    layer: Arc<Layer>,
    channel: String,
    groups: Vec<String>,
}

impl Subscription {
    /// Creates a channel and adds it to `groups`.
    pub(super) async fn join(
        layer: &Arc<Layer>,
        groups: Vec<String>,
    ) -> Result<(Self, mpsc::Receiver<Delivery>)> {
        let (channel, rx) = layer.new_channel();
        // Leaves whichever groups were joined if one of them fails.
        let subscription = Self {
            layer: Arc::clone(layer),
            channel,
            groups,
        };
        subscription.refresh().await?;
        Ok((subscription, rx))
    }

    /// Joins the groups again, refreshing their expiry. Group memberships expire after a day.
    pub(super) async fn refresh(&self) -> Result<()> {
        for group in &self.groups {
            self.layer.group_add(group, &self.channel).await?;
        }
        Ok(())
    }

    /// Leaves the groups and waits until they're left.
    ///
    /// Dropping a subscription leaves them in the background instead, which doesn't happen when
    /// the runtime is shutting down. The memberships then expire after a day.
    pub(super) async fn leave(mut self) {
        self.layer.remove_channel(&self.channel);
        for group in std::mem::take(&mut self.groups) {
            if let Err(err) = self.layer.group_discard(&group, &self.channel).await {
                warn!(?err, group, "failed to leave channel layer group");
            }
        }
    }

    #[cfg(test)]
    pub(super) fn channel(&self) -> &str {
        &self.channel
    }
}

impl Drop for Subscription {
    fn drop(&mut self) {
        self.layer.remove_channel(&self.channel);
        if self.groups.is_empty() {
            return;
        }
        let Ok(runtime) = tokio::runtime::Handle::try_current() else {
            // The memberships expire on their own.
            return;
        };
        let layer = Arc::clone(&self.layer);
        let channel = std::mem::take(&mut self.channel);
        let groups = std::mem::take(&mut self.groups);
        runtime.spawn(async move {
            for group in groups {
                if let Err(err) = layer.group_discard(&group, &channel).await {
                    warn!(?err, group, "failed to leave channel layer group");
                }
            }
        });
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_notification_without_message() {
        let id = Uuid::new_v4();
        let payload = format!("{id}:asgi.rust.abc:1794504361.857123");
        assert_eq!(
            Notification::parse(&payload),
            Some(Notification {
                id,
                channel: "asgi.rust.abc",
                expires: 1_794_504_361.857_123,
            })
        );
    }

    #[test]
    fn parses_notification_with_inlined_message() {
        let id = Uuid::new_v4();
        let payload = format!("{id}:asgi.rust.abc:1794504361:eJxrYGBgYGBg");
        let notification = Notification::parse(&payload).expect("failed to parse");
        assert_eq!(notification.channel, "asgi.rust.abc");
    }

    #[test]
    fn rejects_malformed_notifications() {
        for payload in [
            "",
            "not-a-uuid:channel:1",
            "only-one-part",
            &Uuid::new_v4().to_string(),
        ] {
            assert_eq!(Notification::parse(payload), None, "{payload}");
        }
        let id = Uuid::new_v4();
        assert_eq!(Notification::parse(&format!("{id}:channel:soon")), None);
    }

    #[test]
    fn notifications_in_the_past_are_expired() {
        let past = Notification {
            id: Uuid::new_v4(),
            channel: "c",
            expires: 1.0,
        };
        assert!(past.is_expired());
        let future = Notification {
            expires: 99_999_999_999.0,
            ..past
        };
        assert!(!future.is_expired());
    }

    fn lazy_layer() -> Arc<Layer> {
        let pool = PgPoolOptions::new().connect_lazy("postgres://localhost/unused");
        Arc::new(Layer::new(pool.expect("failed to create lazy pool")))
    }

    #[tokio::test]
    async fn dispatch_delivers_to_registered_channel() {
        let layer = lazy_layer();
        let (channel, mut rx) = layer.new_channel();
        let id = Uuid::new_v4();

        layer.dispatch(&format!("{id}:{channel}:99999999999"));
        layer.dispatch(&format!("{}:asgi.rust.other:99999999999", Uuid::new_v4()));

        match rx.try_recv().expect("expected a delivery") {
            Delivery::Notified(delivered) => assert_eq!(delivered, id),
            Delivery::Claimed(_) => panic!("expected a notified delivery"),
        }
        assert!(
            rx.try_recv().is_err(),
            "only messages for the channel are delivered"
        );
    }

    #[tokio::test]
    async fn dispatch_skips_expired_messages() {
        let layer = lazy_layer();
        let (channel, rx) = layer.new_channel();
        layer.dispatch(&format!("{}:{channel}:1", Uuid::new_v4()));
        assert!(rx.is_empty(), "expired messages are not delivered");
    }

    #[tokio::test]
    async fn full_queue_drops_instead_of_waiting() {
        let layer = lazy_layer();
        let (channel, mut rx) = layer.new_channel();
        for _ in 0..=QUEUE_CAPACITY {
            layer.dispatch(&format!("{}:{channel}:99999999999", Uuid::new_v4()));
        }
        let mut received = 0_usize;
        while rx.try_recv().is_ok() {
            received += 1;
        }
        assert_eq!(received, QUEUE_CAPACITY);
    }

    #[tokio::test]
    async fn dropped_subscription_stops_deliveries() {
        let layer = lazy_layer();
        let (channel, rx) = layer.new_channel();
        // No groups, so dropping it doesn't touch the database.
        drop(Subscription {
            layer: Arc::clone(&layer),
            channel: channel.clone(),
            groups: Vec::new(),
        });
        drop(rx);
        assert!(
            !layer
                .channels
                .read()
                .unwrap_or_else(PoisonError::into_inner)
                .contains_key(&channel)
        );
    }
}
