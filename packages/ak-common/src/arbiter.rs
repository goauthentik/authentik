//! Utilities to manage long running tasks, such as servers and watchers, and events propagated
//! between those tasks.
//!
//! Also manages signals sent to the main process.

use std::{net, os::unix, sync::Arc, time::Duration};

use axum_server::Handle;
use eyre::{Report, Result};
use tokio::{
    signal::unix::{Signal, SignalKind, signal},
    sync::{Mutex, broadcast},
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
async fn watch_signals(streams: SignalStreams, arbiter: Arbiter) -> Result<()> {
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
            _ = term.recv() => {
                info!("signal TERM received");
                arbiter.do_graceful_shutdown().await;
            },
            _ = usr1.recv() => {
                info!("signal USR1 received");
                let _ = arbiter.send_event(SignalKind::user_defined1().into());
            },
            _ = usr2.recv() => {
                info!("signal USR2 received");
                let _ = arbiter.send_event(SignalKind::user_defined2().into());
            },
            () = arbiter.shutdown() => {
                info!("stopping signals watcher");
                return Ok(());
            }
        };
    }
}

/// Manager for long running tasks, such as servers and watchers.
pub struct Tasks {
    tasks: JoinSet<Result<()>>,
    arbiter: Arbiter,
}

impl Tasks {
    /// Create a new [`Tasks`] manager.
    ///
    /// # Errors
    ///
    /// Errors if the creation of signals watcher fails.
    pub fn new() -> Result<Self> {
        let mut tasks = JoinSet::new();
        let arbiter = Arbiter::new(&mut tasks)?;

        Ok(Self { tasks, arbiter })
    }

    /// Build a new task. See [`tokio::task::JoinSet::build_task`] for details.
    pub fn build_task(&mut self) -> Builder<'_, Result<()>> {
        self.tasks.build_task()
    }

    /// Get an [`Arbiter`].
    pub fn arbiter(&self) -> Arbiter {
        self.arbiter.clone()
    }

    /// Run the tasks until completion. If one of them fails, terminate the program immediately.
    pub async fn run(self) -> Vec<Report> {
        let Self { mut tasks, arbiter } = self;

        let mut errors = Vec::new();

        if let Some(result) = tasks.join_next().await {
            arbiter.do_graceful_shutdown().await;

            match result {
                Ok(Ok(())) => {}
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
                    Ok(Ok(())) => {}
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
pub struct Arbiter {
    /// Token to shutdown the application immediately.
    fast_shutdown: CancellationToken,
    /// Token to shutdown the application gracefully.
    graceful_shutdown: CancellationToken,
    /// Token set when any shutdown is triggered.
    shutdown: CancellationToken,

    /// axum-server [`Handle`] to manage.
    net_handles: Arc<Mutex<Vec<Handle<net::SocketAddr>>>>,
    unix_handles: Arc<Mutex<Vec<Handle<unix::net::SocketAddr>>>>,

    /// Broadcaster of program-wide events, except shutdown which is handled by tokens above.
    events_tx: broadcast::Sender<Event>,
}

impl Arbiter {
    fn new(tasks: &mut JoinSet<Result<()>>) -> Result<Self> {
        let (events_tx, _events_rx) = broadcast::channel(1024);
        let arbiter = Self {
            fast_shutdown: CancellationToken::new(),
            graceful_shutdown: CancellationToken::new(),
            shutdown: CancellationToken::new(),

            // 5 is http, https, metrics and a bit of room
            net_handles: Arc::new(Mutex::new(Vec::with_capacity(5))),
            // 2 is http and metrics
            unix_handles: Arc::new(Mutex::new(Vec::with_capacity(2))),

            events_tx,
        };

        let streams = SignalStreams::new()?;

        tasks
            .build_task()
            .name(&format!("{}::watch_signals", module_path!()))
            .spawn(watch_signals(streams, arbiter.clone()))?;

        Ok(arbiter)
    }

    /// Add a new [`Handle`] to be managed, specifically for [`net::SocketAddr`] addresses.
    ///
    /// This handle will be shutdown when this arbiter is shutdown.
    pub async fn add_net_handle(&self, handle: Handle<net::SocketAddr>) {
        self.net_handles.lock().await.push(handle);
    }

    /// Add a new [`Handle`] to be managed, specifically for [`unix::net::SocketAddr`] addresses.
    ///
    /// This handle will be shutdown when this arbiter is shutdown.
    pub async fn add_unix_handle(&self, handle: Handle<unix::net::SocketAddr>) {
        self.unix_handles.lock().await.push(handle);
    }

    /// Future that will complete when the application needs to shutdown immediately.
    ///
    /// Consumers listening on this must also listen on [`Arbiter::graceful_shutdown`], as only one
    /// of those is set upon shutdown.
    ///
    /// It is also possible to use [`Arbiter::shutdown`] when the behaviour is the same between a
    /// fast and a graceful shutdown.
    pub fn fast_shutdown(&self) -> WaitForCancellationFuture<'_> {
        self.fast_shutdown.cancelled()
    }

    /// Future that will complete when the application needs to shutdown gracefully.
    ///
    /// Consumers listening on this must also listen on [`Arbiter::fast_shutdown`], as only one
    /// of those is set upon shutdown.
    ///
    /// It is also possible to use [`Arbiter::shutdown`] when the behaviour is the same between a
    /// fast and a graceful shutdown.
    pub fn graceful_shutdown(&self) -> WaitForCancellationFuture<'_> {
        self.graceful_shutdown.cancelled()
    }

    /// Future that will complete when the application needs to shutdown, either immediately or
    /// gracefully. It's a helper so users that don't make the difference between immediate and
    /// graceful shutdown don't need to handle two scenarios.
    pub fn shutdown(&self) -> WaitForCancellationFuture<'_> {
        self.shutdown.cancelled()
    }

    /// Shutdown the application immediately.
    pub async fn do_fast_shutdown(&self) {
        info!("arbiter has been told to shutdown immediately");
        self.unix_handles
            .lock()
            .await
            .iter()
            .for_each(Handle::shutdown);
        self.net_handles
            .lock()
            .await
            .iter()
            .for_each(Handle::shutdown);
        info!("all webservers have been shutdown, shutting down the other tasks immediately");
        self.fast_shutdown.cancel();
        self.shutdown.cancel();
    }

    /// Shutdown the application gracefully.
    pub async fn do_graceful_shutdown(&self) {
        info!("arbiter has been told to shutdown gracefully");
        // Match the value in lifecycle/gunicorn.conf.py for graceful shutdown
        let timeout = Some(Duration::from_secs(30 + 5));
        self.unix_handles
            .lock()
            .await
            .iter()
            .for_each(|handle| handle.graceful_shutdown(timeout));
        self.net_handles
            .lock()
            .await
            .iter()
            .for_each(|handle| handle.graceful_shutdown(timeout));
        info!("all webservers have been shutdown, shutting down the other tasks gracefully");
        self.graceful_shutdown.cancel();
        self.shutdown.cancel();
    }

    /// Create a new [`broadcast::Receiver`] to listen for signals sent to the main process. This
    /// may not include all signals we catch, since some of those will shutdown the application.
    pub fn events_subscribe(&self) -> broadcast::Receiver<Event> {
        self.events_tx.subscribe()
    }

    /// Send a value on the config changes watch channel.
    ///
    /// # Errors
    ///
    /// See [`broadcast::Sender::send`].
    pub fn send_event(&self, value: Event) -> Result<usize, broadcast::error::SendError<Event>> {
        self.events_tx.send(value)
    }
}

/// Events propagated throughout the program.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Event {
    /// A signal has been received.
    Signal(SignalKind),
    /// The configuration has been reloaded from sources.
    ConfigChanged,
}

impl From<SignalKind> for Event {
    fn from(value: SignalKind) -> Self {
        Self::Signal(value)
    }
}

#[cfg(test)]
mod tests {
    mod events {
        use nix::sys::signal::{Signal, raise};
        use tokio::time::sleep;

        use super::super::*;

        async fn signal_self(signal: Signal) {
            raise(signal).expect("failed to send signal");
            sleep(Duration::from_millis(50)).await;
        }

        #[tokio::test]
        async fn signals_hup() {
            let tasks = Tasks::new().expect("tasks to create successfully");
            let arbiter = tasks.arbiter();

            signal_self(Signal::SIGHUP).await;

            assert!(arbiter.fast_shutdown.is_cancelled());
            assert!(!arbiter.graceful_shutdown.is_cancelled());
            assert!(arbiter.shutdown.is_cancelled());
            assert_eq!(tasks.run().await.len(), 0);
        }

        #[tokio::test]
        async fn signals_quit() {
            let tasks = Tasks::new().expect("tasks to create successfully");
            let arbiter = tasks.arbiter();

            signal_self(Signal::SIGQUIT).await;

            assert!(arbiter.fast_shutdown.is_cancelled());
            assert!(!arbiter.graceful_shutdown.is_cancelled());
            assert!(arbiter.shutdown.is_cancelled());
            assert_eq!(tasks.run().await.len(), 0);
        }

        #[tokio::test]
        async fn signals_int() {
            let tasks = Tasks::new().expect("tasks to create successfully");
            let arbiter = tasks.arbiter();

            signal_self(Signal::SIGINT).await;

            assert!(arbiter.fast_shutdown.is_cancelled());
            assert!(!arbiter.graceful_shutdown.is_cancelled());
            assert!(arbiter.shutdown.is_cancelled());
            assert_eq!(tasks.run().await.len(), 0);
        }

        #[tokio::test]
        async fn signals_term() {
            let tasks = Tasks::new().expect("tasks to create successfully");
            let arbiter = tasks.arbiter();

            signal_self(Signal::SIGTERM).await;

            assert!(!arbiter.fast_shutdown.is_cancelled());
            assert!(arbiter.graceful_shutdown.is_cancelled());
            assert!(arbiter.shutdown.is_cancelled());
            assert_eq!(tasks.run().await.len(), 0);
        }

        #[tokio::test]
        async fn signals_other_no_listener() {
            let tasks = Tasks::new().expect("tasks to create successfully");
            let arbiter = tasks.arbiter();

            signal_self(Signal::SIGUSR1).await;
            signal_self(Signal::SIGUSR2).await;

            arbiter.do_fast_shutdown().await;
            assert_eq!(tasks.run().await.len(), 0);
        }

        #[tokio::test]
        async fn signals_usr1() {
            let tasks = Tasks::new().expect("tasks to create successfully");
            let arbiter = tasks.arbiter();
            let mut events_rx = arbiter.events_subscribe();

            signal_self(Signal::SIGUSR1).await;

            assert_eq!(
                events_rx.recv().await.expect("failed to receive event"),
                Event::Signal(SignalKind::user_defined1())
            );
        }

        #[tokio::test]
        async fn signals_usr2() {
            let tasks = Tasks::new().expect("tasks to create successfully");
            let arbiter = tasks.arbiter();
            let mut events_rx = arbiter.events_subscribe();

            signal_self(Signal::SIGUSR2).await;

            assert_eq!(
                events_rx.recv().await.expect("failed to receive event"),
                Event::Signal(SignalKind::user_defined2()),
            );
        }

        #[tokio::test]
        async fn events() {
            let tasks = Tasks::new().expect("tasks to create successfully");
            let arbiter = tasks.arbiter();
            let mut events_rx1 = arbiter.events_subscribe();
            let mut events_rx2 = arbiter.events_subscribe();

            let _ = arbiter.send_event(Event::ConfigChanged);

            assert_eq!(
                events_rx1.recv().await.expect("failed to receive event"),
                Event::ConfigChanged,
            );
            assert_eq!(
                events_rx2.recv().await.expect("failed to receive event"),
                Event::ConfigChanged,
            );
        }
    }

    mod tasks {
        use eyre::eyre;

        use super::super::*;

        async fn success_task(arbiter: Arbiter) -> Result<()> {
            tokio::select! {
                () = arbiter.fast_shutdown() => {},
                () = arbiter.graceful_shutdown() => {},
            }
            Ok(())
        }

        async fn error_task(arbiter: Arbiter) -> Result<()> {
            arbiter.shutdown().await;
            Err(eyre!("error"))
        }

        #[tokio::test]
        async fn successful_tasks() {
            let mut tasks = Tasks::new().expect("tasks to create successfully");
            let arbiter = tasks.arbiter();

            for _ in 0..10_u8 {
                tasks
                    .build_task()
                    .spawn(success_task(arbiter.clone()))
                    .expect("failed to spawn task");
            }
            arbiter.do_fast_shutdown().await;

            assert_eq!(tasks.run().await.len(), 0);
        }

        #[tokio::test]
        async fn error_tasks() {
            let mut tasks = Tasks::new().expect("tasks to create successfully");
            let arbiter = tasks.arbiter();

            for _ in 0..10_u8 {
                tasks
                    .build_task()
                    .spawn(error_task(arbiter.clone()))
                    .expect("failed to spawn task");
            }
            arbiter.do_fast_shutdown().await;

            assert_eq!(tasks.run().await.len(), 10);
        }
    }
}
