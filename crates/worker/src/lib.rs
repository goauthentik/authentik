use std::{ffi::CStr, process::exit};

use clap::Parser;
use color_eyre::eyre::Result;
use pyo3::{ffi::c_str, prelude::*};

shadow_rs::shadow!(build);

#[derive(Debug, Parser)]
#[command(version = build::CLAP_LONG_VERSION, about, long_about = None)]
pub struct Cli {}

const DRAMATIQ_ARGS: &CStr = c_str!(include_str!(concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/src/dramatiq_args.py"
)));

pub fn run(_cli: Cli) -> Result<()> {
    Python::initialize();
    let exit_code = Python::attach(|py| {
        let setup = PyModule::import(py, "authentik.root.setup")?;
        setup.getattr("setup")?.call0()?;
        let lifecycle = PyModule::import(py, "lifecycle.migrate")?;
        lifecycle.getattr("run_migrations")?.call0()?;
        let django_db = PyModule::import(py, "django.db")?;

        let dramatiq_args = PyModule::from_code(
            py,
            DRAMATIQ_ARGS,
            c_str!("dramatiq_args.py"),
            c_str!("dramatiq_args"),
        )?;
        let args = dramatiq_args.getattr("args")?;

        django_db
            .getattr("connections")?
            .getattr("close_all")?
            .call0()?;

        let dramatiq_cli = PyModule::import(py, "dramatiq.cli")?;
        let exit_code: i32 = dramatiq_cli.call_method1("main", (args,))?.extract()?;

        Ok::<_, color_eyre::eyre::Error>(exit_code)
    })?;

    exit(exit_code);
}
