//! Tests against the database, with the tables and trigger the Python migrations create.

use std::{
    sync::{Arc, atomic::Ordering},
    time::Duration,
};

use ak_common::{Tasks, config, config::schema::RustWebsocketRoute, db};
use futures::StreamExt as _;
use serde_json::{Value, json};
use tempfile::TempDir;
use tokio::{net::TcpListener, time::timeout};
use tokio_tungstenite::tungstenite::{Error as WsError, Message};
use uuid::Uuid;

use super::{
    WebsocketState,
    codec::tests::{PYTHON_NOTIFICATION, python_notification},
    contract::{self, tests::spawn_python},
    layer::{Delivery, Layer, Subscription},
    router,
};
use crate::server::GUNICORN_READY;

const WAIT: Duration = Duration::from_secs(10);

async fn setup() -> Tasks {
    config::init().expect("failed to init config");
    let mut tasks = Tasks::new().expect("failed to create tasks");
    db::init(&mut tasks).await.expect("failed to init db");
    tasks
}

async fn start_layer(tasks: &mut Tasks) -> Arc<Layer> {
    let layer = Arc::new(Layer::new(db::get().clone()));
    let arbiter = tasks.arbiter();
    tasks
        .build_task()
        .name("layer")
        .spawn(Arc::clone(&layer).run(arbiter))
        .expect("failed to spawn layer");
    timeout(WAIT, layer.wait_listening())
        .await
        .expect("the layer never started listening");
    layer
}

fn unique_group() -> String {
    format!("test-{}", Uuid::new_v4().simple())
}

/// What `group_send_blocking` does in Python: one message row for each channel in the group.
async fn python_group_send(group: &str, message: &[u8]) -> u64 {
    sqlx::query(
        "INSERT INTO django_channels_postgres_message (id, channel, message, expires)
        SELECT gen_random_uuid(), channel, $2, now() + interval '1 minute'
        FROM django_channels_postgres_groupchannel
        WHERE group_key = $1 AND expires >= now()",
    )
    .bind(format!("asgi.group.{group}"))
    .bind(message)
    .execute(db::get())
    .await
    .expect("failed to send to group")
    .rows_affected()
}

async fn group_members(group: &str) -> Vec<String> {
    sqlx::query_scalar(
        "SELECT channel FROM django_channels_postgres_groupchannel WHERE group_key = $1",
    )
    .bind(format!("asgi.group.{group}"))
    .fetch_all(db::get())
    .await
    .expect("failed to query group")
}

#[tokio::test]
async fn python_group_send_reaches_rust_channel() {
    let mut tasks = setup().await;
    let layer = start_layer(&mut tasks).await;
    let group = unique_group();

    let (subscription, mut deliveries) = Subscription::join(&layer, vec![group.clone()])
        .await
        .expect("failed to join");
    assert_eq!(group_members(&group).await, [subscription.channel()]);

    assert_eq!(python_group_send(&group, PYTHON_NOTIFICATION).await, 1);

    let delivery = timeout(WAIT, deliveries.recv())
        .await
        .expect("no message arrived")
        .expect("channel closed");
    let message = layer
        .claim(delivery)
        .await
        .expect("failed to claim")
        .expect("message was already claimed");
    assert_eq!(Value::Object(message), python_notification());

    let remaining: i64 = sqlx::query_scalar(
        "SELECT count(*) FROM django_channels_postgres_message WHERE channel = $1",
    )
    .bind(subscription.channel())
    .fetch_one(db::get())
    .await
    .expect("failed to count messages");
    assert_eq!(remaining, 0, "claiming a message deletes it");

    subscription.leave().await;
    assert_eq!(
        group_members(&group).await,
        Vec::<String>::new(),
        "leaving removes the membership"
    );
}

#[tokio::test]
async fn catches_up_on_messages_sent_before_listening() {
    let mut tasks = setup().await;
    let layer = Arc::new(Layer::new(db::get().clone()));
    let group = unique_group();
    let (subscription, mut deliveries) = Subscription::join(&layer, vec![group.clone()])
        .await
        .expect("failed to join");
    assert_eq!(python_group_send(&group, PYTHON_NOTIFICATION).await, 1);

    let arbiter = tasks.arbiter();
    tasks
        .build_task()
        .name("layer")
        .spawn(Arc::clone(&layer).run(arbiter))
        .expect("failed to spawn layer");

    let delivery = timeout(WAIT, deliveries.recv())
        .await
        .expect("no message arrived")
        .expect("channel closed");
    assert!(matches!(delivery, Delivery::Claimed(_)));
    let message = layer
        .claim(delivery)
        .await
        .expect("failed to decode")
        .expect("caught up messages are already claimed");
    assert_eq!(Value::Object(message), python_notification());

    subscription.leave().await;
}

/// Dropping a subscription without leaving, like a connection task that panicked, still
/// leaves its groups.
#[tokio::test]
async fn dropping_subscription_leaves_groups() {
    let _tasks = setup().await;
    let layer = Arc::new(Layer::new(db::get().clone()));
    let group = unique_group();
    let (subscription, _deliveries) = Subscription::join(&layer, vec![group.clone()])
        .await
        .expect("failed to join");
    assert_eq!(group_members(&group).await.len(), 1);

    drop(subscription);

    timeout(WAIT, async {
        while !group_members(&group).await.is_empty() {
            tokio::time::sleep(Duration::from_millis(20)).await;
        }
    })
    .await
    .expect("the group membership was never removed");
}

/// Serves the WebSocket routes on a local port, with a stand-in for gunicorn that answers
/// authorizations with `authorization`.
async fn serve(tasks: &mut Tasks, authorization: Value) -> (String, TempDir) {
    let layer = start_layer(tasks).await;
    let dir = TempDir::new().expect("failed to create temp dir");
    let socket_path = dir.path().join("authentik-gunicorn.sock");
    spawn_python(&socket_path, 200, &authorization);
    GUNICORN_READY.store(true, Ordering::Relaxed);

    let app = router(
        Arc::new(WebsocketState {
            contract: contract::Contract::new(contract::tests::client(&socket_path)),
            layer,
            arbiter: tasks.arbiter(),
        }),
        &[RustWebsocketRoute::Client],
    );
    let listener = TcpListener::bind("127.0.0.1:0")
        .await
        .expect("failed to bind");
    let addr = listener.local_addr().expect("no local address");
    tokio::spawn(async move { axum::serve(listener, app).await });
    (format!("ws://{addr}/ws/client/"), dir)
}

#[tokio::test]
async fn browser_receives_notifications() {
    let mut tasks = setup().await;
    let group = unique_group();
    let (url, _dir) = serve(&mut tasks, json!({"accept": true, "groups": [group]})).await;

    let (mut socket, response) = tokio_tungstenite::connect_async(url)
        .await
        .expect("failed to connect");
    assert!(
        !response.headers().contains_key("sec-websocket-protocol"),
        "no subprotocol was requested, so none is selected"
    );
    assert_eq!(group_members(&group).await.len(), 1);

    assert_eq!(python_group_send(&group, PYTHON_NOTIFICATION).await, 1);

    let message = timeout(WAIT, socket.next())
        .await
        .expect("no message arrived")
        .expect("socket closed")
        .expect("socket failed");
    let Message::Text(text) = message else {
        panic!("expected a text message, got {message:?}");
    };
    let mut expected = python_notification();
    expected["message_type"] = json!("notification.new");
    assert_eq!(
        serde_json::from_str::<Value>(&text).expect("invalid JSON"),
        expected,
        "the message matches what ClientConsumer sends"
    );

    socket.close(None).await.expect("failed to close");
    timeout(WAIT, async {
        while !group_members(&group).await.is_empty() {
            tokio::time::sleep(Duration::from_millis(20)).await;
        }
    })
    .await
    .expect("closing the connection never left the group");
}

#[tokio::test]
async fn denied_handshake_is_forbidden() {
    let mut tasks = setup().await;
    let (url, _dir) = serve(&mut tasks, json!({"accept": false, "groups": []})).await;

    let err = tokio_tungstenite::connect_async(url)
        .await
        .expect_err("the handshake must be denied");
    let WsError::Http(response) = err else {
        panic!("expected an HTTP error, got {err:?}");
    };
    assert_eq!(response.status(), 403);
}
