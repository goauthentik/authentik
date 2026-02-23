//! Utilities to manage long running tasks, such as servers and watchers.
//!
//! Also manages signals sent to the main process.

use std::{net::SocketAddr, sync::Arc, time::Duration};

use axum_server::Handle;
use eyre::{Report, Result};
use tokio::{
    signal::unix::{Signal, SignalKind, signal},
    sync::{Mutex, broadcast, watch},
    task::{JoinSet, join_set::Builder},
};
use tokio_util::sync::{CancellationToken, WaitForCancellationFuture};
use tracing::info;

/// All the signal streams we watch for. We don't create those directly in [`watch_signals`]
/// because that would prevent us from handling errors early.
struct SignalStreams {
    hup: Signal,
    int: Signal,
    quit: Signal,
    usr1: Signal,
    usr2: Signal,
    term: Signal,
}

impl SignalStreams {
    fn new() -> Result<Self> {
        Ok(Self {
            hup: signal(SignalKind::hangup())?,
            int: signal(SignalKind::interrupt())?,
            quit: signal(SignalKind::quit())?,
            usr1: signal(SignalKind::user_defined1())?,
            usr2: signal(SignalKind::user_defined2())?,
            term: signal(SignalKind::terminate())?,
        })
    }
}

/// Watch for incoming signals and either shutdown the application or dispatch them to receivers.
async fn watch_signals(
    streams: SignalStreams,
    arbiter: Arbiter,
    _signals_rx: broadcast::Receiver<SignalKind>,
) -> Result<()> {
    info!("starting signals watcher");
    let SignalStreams {
        mut hup,
        mut int,
        mut quit,
        mut usr1,
        mut usr2,
        mut term,
    } = streams;
    loop {
        tokio::select! {
            _ = hup.recv() => {
                info!("signal HUP received");
                arbiter.do_fast_shutdown().await;
            },
            _ = int.recv() => {
                info!("signal INT received");
                arbiter.do_fast_shutdown().await;
            },
            _ = quit.recv() => {
                info!("signal QUIT received");
                arbiter.do_fast_shutdown().await;
            },
            _ = usr1.recv() => {
                info!("signal URS1 received");
                arbiter.signals_tx.send(SignalKind::user_defined1())?;
            },
            _ = usr2.recv() => {
                info!("USR2 received.");
                arbiter.signals_tx.send(SignalKind::user_defined2())?;
            },
            _ = term.recv() => {
                info!("signal TERM received");
                arbiter.do_graceful_shutdown().await;
            },
            _ = arbiter.shutdown() => {
                info!("stopping signals watcher");
                return Ok(());
            }
        };
    }
}

/// Manager for long running tasks, such as servers and watchers.
pub(crate) struct Tasks {
    pub(crate) tasks: JoinSet<Result<()>>,
    arbiter: Arbiter,
}

impl Tasks {
    pub(crate) fn new() -> Result<Self> {
        let mut tasks = JoinSet::new();
        let arbiter = Arbiter::new(&mut tasks)?;

        Ok(Self { tasks, arbiter })
    }

    /// Build a new task. See [`tokio::task::JoinSet::build_task`] for details.
    pub(crate) fn build_task(&mut self) -> Builder<'_, Result<()>> {
        self.tasks.build_task()
    }

    /// Get an [`Arbiter`]
    pub(crate) fn arbiter(&self) -> Arbiter {
        self.arbiter.clone()
    }

    pub(crate) async fn run(self) -> Vec<Report> {
        let Self { mut tasks, arbiter } = self;

        let mut errors = Vec::new();

        if let Some(result) = tasks.join_next().await {
            arbiter.do_graceful_shutdown().await;

            match result {
                Ok(Ok(_)) => {}
                Ok(Err(err)) => {
                    arbiter.do_fast_shutdown().await;
                    errors.push(err);
                }
                Err(err) => {
                    arbiter.do_fast_shutdown().await;
                    errors.push(Report::new(err));
                }
            }

            while let Some(result) = tasks.join_next().await {
                match result {
                    Ok(Ok(_)) => {}
                    Ok(Err(err)) => errors.push(err),
                    Err(err) => errors.push(Report::new(err)),
                }
            }
        }

        errors
    }
}

/// Manage shutdown state and several communication channels.
#[derive(Clone)]
pub(crate) struct Arbiter {
    /// Token to shutdown the application immediately.
    fast_shutdown: CancellationToken,
    /// Token to shutdown the application gracefully.
    graceful_shutdown: CancellationToken,
    /// Token set when any shutdown is triggered.
    shutdown: CancellationToken,

    /// Axum handles to manage
    handles: Arc<Mutex<Vec<Handle<SocketAddr>>>>,

    /// Broadcaster of signals sent to the main process.
    signals_tx: broadcast::Sender<SignalKind>,
    /// Watcher of config change events
    config_changed_tx: watch::Sender<()>,
    _config_changed_rx: watch::Receiver<()>,
    /// Watcher for gunicorn ready event
    gunicorn_ready_tx: watch::Sender<()>,
    _gunicorn_ready_rx: watch::Receiver<()>,
}

impl Arbiter {
    fn new(tasks: &mut JoinSet<Result<()>>) -> Result<Self> {
        let (signals_tx, signals_rx) = broadcast::channel(10);
        let (config_changed_tx, _config_changed_rx) = watch::channel(());
        let (gunicorn_ready_tx, _gunicorn_ready_rx) = watch::channel(());
        let arbiter = Self {
            fast_shutdown: CancellationToken::new(),
            graceful_shutdown: CancellationToken::new(),
            shutdown: CancellationToken::new(),

            // 5 is http, https, metrics and a bit of room
            handles: Arc::new(Mutex::new(Vec::with_capacity(5))),

            signals_tx,
            config_changed_tx,
            _config_changed_rx,
            gunicorn_ready_tx,
            _gunicorn_ready_rx,
        };

        let streams = SignalStreams::new()?;

        tasks
            .build_task()
            .name(&format!("{}::watch_signals", module_path!()))
            .spawn(watch_signals(streams, arbiter.clone(), signals_rx))?;

        Ok(arbiter)
    }

    pub(crate) async fn add_handle(&self, handle: Handle<SocketAddr>) {
        self.handles.lock().await.push(handle);
    }

    /// Future that will complete when the application needs to shutdown immediately.
    pub(crate) fn fast_shutdown(&self) -> WaitForCancellationFuture<'_> {
        self.fast_shutdown.cancelled()
    }

    /// Future that will complete when the application needs to shutdown gracefully.
    pub(crate) fn graceful_shutdown(&self) -> WaitForCancellationFuture<'_> {
        self.graceful_shutdown.cancelled()
    }

    /// Future that will complete when the application needs to shutdown, either immediately or
    /// gracefully. It's a helper so users that don't make the difference between immediate and
    /// graceful shutdown don't need to handle two scenarios.
    pub(crate) fn shutdown(&self) -> WaitForCancellationFuture<'_> {
        self.shutdown.cancelled()
    }

    /// Shutdown the application immediately.
    async fn do_fast_shutdown(&self) {
        info!("arbiter has been told to shutdown immediately");
        self.handles
            .lock()
            .await
            .iter()
            .for_each(|handle| handle.shutdown());
        info!("all webservers have been shutdown, shutting down the other tasks immediately");
        self.fast_shutdown.cancel();
        self.shutdown.cancel();
    }

    /// Shutdown the application gracefully.
    async fn do_graceful_shutdown(&self) {
        info!("arbiter has been told to shutdown gracefully");
        self.handles
            .lock()
            .await
            .iter()
            // TODO: make configurable
            .for_each(|handle| handle.graceful_shutdown(Some(Duration::from_secs(30))));
        info!("all webservers have been shutdown, shutting down the other tasks gracefully");
        self.graceful_shutdown.cancel();
        self.shutdown.cancel();
    }

    /// Create a new [`broadcast::Receiver`] to listen for signals sent to the main process. This
    /// may not include all signals we catch, since some of those will shutdown the application.
    pub(crate) fn signals_subscribe(&self) -> broadcast::Receiver<SignalKind> {
        self.signals_tx.subscribe()
    }

    /// Send a value on the config changes watch channel
    pub(crate) fn config_changed_send(&self, value: ()) -> Result<()> {
        self.config_changed_tx.send(value)?;
        Ok(())
    }

    /// Create a new [`watch::Receiver`] to listen for detected configuration changes.
    pub(crate) fn config_changed_subscribe(&self) -> watch::Receiver<()> {
        self.config_changed_tx.subscribe()
    }

    /// Send a value on the gunicorn ready watch channel
    pub(crate) fn gunicorn_ready_send(&self, value: ()) -> Result<()> {
        self.gunicorn_ready_tx.send(value)?;
        Ok(())
    }

    /// Create a new [`watch::Receiver`] to listen for gunicorn ready event.
    pub(crate) fn gunicorn_ready_subscribe(&self) -> watch::Receiver<()> {
        self.gunicorn_ready_tx.subscribe()
    }
}
