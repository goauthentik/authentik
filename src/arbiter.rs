//! Utilities to manage long running tasks, such as servers and watchers.
//!
//! Also manages signals sent to the main process.

use eyre::{Report, Result};
use tokio::{
    signal::unix::{Signal, SignalKind, signal},
    sync::broadcast,
    task::{JoinSet, join_set::Builder},
};
use tokio_util::sync::{CancellationToken, WaitForCancellationFuture};

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
            _ = hup.recv() => { arbiter.fast_shutdown.cancel(); },
            _ = int.recv() => { arbiter.fast_shutdown.cancel(); },
            _ = quit.recv() => { arbiter.fast_shutdown.cancel(); },
            _ = usr1.recv() => { arbiter.signals_tx.send(SignalKind::user_defined1())?; },
            _ = usr2.recv() => { arbiter.signals_tx.send(SignalKind::user_defined2())?; },
            _ = term.recv() => { arbiter.graceful_shutdown.cancel(); },
            _ = arbiter.shutdown() => return Ok(()),
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
            arbiter.do_graceful_shutdown();

            match result {
                Ok(Ok(_)) => {}
                Ok(Err(err)) => {
                    arbiter.do_fast_shutdown();
                    errors.push(err);
                }
                Err(err) => {
                    arbiter.do_fast_shutdown();
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

    /// Broadcaster of signals sent to the main process.
    signals_tx: broadcast::Sender<SignalKind>,
}

impl Arbiter {
    fn new(tasks: &mut JoinSet<Result<()>>) -> Result<Self> {
        let (signals_tx, signals_rx) = broadcast::channel(10);
        let arbiter = Self {
            fast_shutdown: CancellationToken::new(),
            graceful_shutdown: CancellationToken::new(),
            shutdown: CancellationToken::new(),

            signals_tx,
        };

        let streams = SignalStreams::new()?;

        tasks
            .build_task()
            .name(&format!("{}::watch_signals", module_path!()))
            .spawn(watch_signals(streams, arbiter.clone(), signals_rx))?;

        Ok(arbiter)
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
    pub(crate) fn do_fast_shutdown(&self) {
        self.fast_shutdown.cancel();
        self.shutdown.cancel();
    }

    /// Shutdown the application gracefully.
    pub(crate) fn do_graceful_shutdown(&self) {
        self.graceful_shutdown.cancel();
        self.shutdown.cancel();
    }

    /// Create a new [`broadcast::Receiver`] to listen for signals sent to the main process. This
    /// may not include all signals we catch, since some of those will shutdown the application.
    pub(crate) fn signals_subscribe(&self) -> broadcast::Receiver<SignalKind> {
        self.signals_tx.subscribe()
    }
}
