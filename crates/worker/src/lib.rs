use std::{collections::HashMap, process::exit, sync::Arc, thread, thread::sleep, time::Duration};

use clap::Parser;
use color_eyre::eyre::Result;
use nix::{
    sys::signal::{SigSet, SigmaskHow, Signal, kill, pthread_sigmask},
    unistd::Pid,
};
use pyo3::{IntoPyObjectExt, prelude::*, types::IntoPyDict};
use std::sync::atomic::{AtomicBool, Ordering};

shadow_rs::shadow!(build);

#[derive(Debug, Parser)]
#[command(version = build::CLAP_LONG_VERSION, about, long_about = None)]
pub struct Cli {}

fn handled_signals() -> SigSet {
    let mut sigset = SigSet::empty();
    sigset.add(Signal::SIGINT);
    sigset.add(Signal::SIGTERM);
    sigset.add(Signal::SIGHUP);
    sigset
}

#[pyfunction]
fn worker_process(worker_id: u32, logging_pipe: Py<PyAny>, event: Py<PyAny>) {
    let running = Arc::new(AtomicBool::new(true));

    unsafe { signal_hook::low_level::register(signal_hook::consts::SIGINT, || {}) }.unwrap();
    for sig in [signal_hook::consts::SIGTERM, signal_hook::consts::SIGHUP] {
        signal_hook::flag::register_conditional_shutdown(sig, 0, Arc::clone(&running)).unwrap();
        signal_hook::flag::register(sig, Arc::clone(&running)).unwrap();
    }
    pthread_sigmask(SigmaskHow::SIG_UNBLOCK, Some(&handled_signals()), None).unwrap();

    let res: Result<(), PyErr> = Python::attach(|py| {
        let dramatiq_broker = PyModule::import(py, "dramatiq.broker")?;
        let dramatiq_worker = PyModule::import(py, "dramatiq.worker")?;
        let random = PyModule::import(py, "random")?;

        random.call_method0("seed")?;

        let broker = dramatiq_broker.call_method0("get_broker")?;
        broker.call_method1("emit_after", ("process_boot",))?;

        let worker = dramatiq_worker.call_method(
            "Worker",
            (&broker,),
            Some(
                &[
                    ("queues", None::<()>.into_bound_py_any(py)?),
                    ("worker_threads", 1.into_bound_py_any(py)?),
                ]
                .into_py_dict(py)?,
            ),
        )?;
        worker.setattr("worker_id", worker_id)?;
        worker.call_method0("start")?;

        event.call_method0(py, "set")?;

        while running.load(Ordering::Relaxed) {
            sleep(Duration::from_millis(500));
        }

        worker.call_method(
            "stop",
            (),
            Some(&[("timeout", 600_000.into_bound_py_any(py)?)].into_py_dict(py)?),
        )?;

        broker.call_method0("close")?;

        Ok(())
    });

    if res.is_err() {
        exit(1);
    }
}

pub fn run(_cli: Cli) -> Result<()> {
    Python::initialize();
    Python::attach(|py| {
        let setup = PyModule::import(py, "authentik.root.setup")?;
        setup.getattr("setup")?.call0()?;
        let lifecycle = PyModule::import(py, "lifecycle.migrate")?;
        lifecycle.getattr("run_migrations")?.call0()?;
        let django_db = PyModule::import(py, "django.db")?;
        django_db
            .getattr("connections")?
            .getattr("close_all")?
            .call0()?;

        pthread_sigmask(SigmaskHow::SIG_BLOCK, Some(&handled_signals()), None)?;

        let multiprocessing = PyModule::import(py, "multiprocessing")?;
        let os = PyModule::import(py, "os")?;

        let mut worker_pipes = vec![];
        let mut worker_processes = vec![];
        let mut worker_process_events = vec![];

        let pipe_result = multiprocessing.call_method(
            "Pipe",
            (),
            Some(&[("duplex", false)].into_py_dict(py)?),
        )?;
        let (read_pipe, write_pipe): (Py<PyAny>, Py<PyAny>) = pipe_result.extract()?;
        let event = multiprocessing.call_method0("Event")?;
        let streamable_pipe = py
            .import("dramatiq.compat")?
            .call_method1("StreamablePipe", (write_pipe.clone_ref(py),))?;

        let process_class = multiprocessing.getattr("Process")?;

        let worker_process_mod = PyModule::new(py, "worker_process")?;
        worker_process_mod.add_function(wrap_pyfunction!(worker_process, &worker_process_mod)?)?;

        let proc = process_class.call(
            (),
            Some(
                &[
                    ("target", worker_process_mod.getattr("worker_process")?),
                    (
                        "args",
                        (0, streamable_pipe, event.clone()).into_bound_py_any(py)?,
                    ),
                    ("daemon", false.into_bound_py_any(py)?),
                ]
                .into_py_dict(py)?,
            ),
        )?;
        proc.call_method0("start")?;
        write_pipe.call_method0(py, "close")?;
        worker_pipes.push(read_pipe);
        worker_processes.push(proc);
        worker_process_events.push(event);

        drop(lifecycle);
        drop(django_db);
        drop(worker_process_mod);

        let mut running = true;
        let term = Arc::new(AtomicBool::new(false));

        for sig in [
            signal_hook::consts::SIGTERM,
            signal_hook::consts::SIGHUP,
            signal_hook::consts::SIGINT,
        ] {
            signal_hook::flag::register(sig, Arc::clone(&term)).unwrap();
        }
        pthread_sigmask(SigmaskHow::SIG_UNBLOCK, Some(&handled_signals()), None).unwrap();

        sleep(Duration::from_secs(10));
        let mut waited = false;
        while !waited
            || worker_processes
                .iter()
                .any(|proc| proc.getattr_opt("exitcode").unwrap().is_none())
        {
            waited = true;
            if term.load(Ordering::Relaxed) {
                running = false;
            }

            for proc in worker_processes.iter() {
                if !running {
                    let _ = os
                        .call_method1("kill", (proc.getattr("pid")?, signal_hook::consts::SIGTERM));
                }

                proc.call_method(
                    "join",
                    (),
                    Some(&[("timeout", 0.5.into_bound_py_any(py)?)].into_py_dict(py)?),
                )?;
                if proc.getattr_opt("exitcode")?.is_none() {
                    continue;
                }

                if running {
                    running = false;
                }
            }
        }

        Ok::<(), color_eyre::eyre::Error>(())
    })?;

    Ok(())
}
//
// struct Worker {
//     processes: Vec<Py<PyAny>>,
//     process_events: Vec<Py<PyAny>>,
//     pipes: Vec<Py<PyAny>>,
// }
//
// impl Worker {
//     fn setup() -> Result<Self> {
//         let mut worker_pipes = vec![];
//         let mut worker_processes = vec![];
//         let mut worker_process_events = vec![];
//
//         Python::initialize();
//         let res: Result<_, color_eyre::eyre::Error> = Python::attach(|py| {
//             let setup = PyModule::import(py, "authentik.root.setup")?;
//             setup.getattr("setup")?.call0()?;
//             let lifecycle = PyModule::import(py, "lifecycle.migrate")?;
//             lifecycle.getattr("run_migrations")?.call0()?;
//             let django_db = PyModule::import(py, "django.db")?;
//             django_db
//                 .getattr("connections")?
//                 .getattr("close_all")?
//                 .call0()?;
//
//             pthread_sigmask(SigmaskHow::SIG_BLOCK, Some(&handled_signals()), None)?;
//
//             let multiprocessing = PyModule::import(py, "multiprocessing")?;
//
//             let pipe_result = multiprocessing.call_method(
//                 "Pipe",
//                 (),
//                 Some(&[("duplex", false)].into_py_dict(py)?),
//             )?;
//             let (read_pipe, write_pipe): (Py<PyAny>, Py<PyAny>) = pipe_result.extract()?;
//             let event = multiprocessing.call_method0("Event")?;
//             let streamable_pipe = py
//                 .import("dramatiq.compat")?
//                 .call_method1("StreamablePipe", (write_pipe.clone_ref(py),))?;
//
//             let process_class = multiprocessing.getattr("Process")?;
//
//             let worker_process_mod = PyModule::new(py, "worker_process")?;
//             worker_process_mod
//                 .add_function(wrap_pyfunction!(worker_process, &worker_process_mod)?)?;
//
//             let proc = process_class.call(
//                 (),
//                 Some(
//                     &[
//                         ("target", worker_process_mod.getattr("worker_process")?),
//                         (
//                             "args",
//                             (0, streamable_pipe, event.clone()).into_bound_py_any(py)?,
//                         ),
//                         ("daemon", false.into_bound_py_any(py)?),
//                     ]
//                     .into_py_dict(py)?,
//                 ),
//             )?;
//
//             proc.call_method0("start")?;
//             worker_processes.push(proc.unbind());
//             worker_pipes.push(read_pipe);
//             worker_process_events.push(event.unbind());
//             write_pipe.call_method0(py, "close")?;
//
//             Ok(())
//         });
//
//         let worker = Self {
//             processes: worker_processes,
//             process_events: worker_process_events,
//             pipes: worker_pipes,
//         };
//         if res.is_err() {
//             worker.shutdown()?;
//             res?;
//         }
//         Ok(worker)
//     }
//
//     fn shutdown(self) -> Result<()> {
//         for
//     }
// }

struct WorkerManager {
    workers: HashMap<i32, WorkerHandle>,
    monitor_thread: Option<thread::JoinHandle<()>>,
    shutdown: Arc<AtomicBool>,
}

struct WorkerHandle {
    process: Py<PyAny>,
    stdout_thread: Option<thread::JoinHandle<()>>,
    stderr_thread: Option<thread::JoinHandle<()>>,
}

impl WorkerManager {
    fn new() -> Self {
        Self {
            workers: HashMap::new(),
            monitor_thread: None,
            shutdown: Arc::new(AtomicBool::new(false)),
        }
    }

    fn start_workers(&mut self, py: Python, processes: usize) -> Result<()> {
        Python::attach(|py| {
            let multiprocessing = py.import("multiprocessing")?;

            for i in 0..processes {
                match self.start_worker(py, i, multiprocessing.clone()) {
                    Ok((pid, handle)) => {
                        self.workers.insert(pid, handle);
                    }
                    Err(e) => {
                        self.shutdown(py);
                        return Err(e);
                    }
                }
            }

            Ok(())
        })?;
        Ok(())
    }

    fn start_worker(
        &self,
        py: Python,
        worker_id: usize,
        multiprocess: Bound<'_, PyModule>,
    ) -> Result<(i32, WorkerHandle)> {
        todo!()
    }

    fn monitor_workers(&mut self) {}

    fn shutdown(&self, py: Python) {}
}
