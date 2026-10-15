//! Container entrypoint

use std::{
    fs,
    os::unix::{
        fs::{MetadataExt as _, PermissionsExt as _},
        process::CommandExt as _,
    },
    path::{Path, PathBuf},
    process::Command,
    time::Duration,
};

use ak_common::config;
use argh::FromArgs;
use eyre::{Result, WrapErr as _, eyre};
#[cfg(target_os = "linux")]
use nix::unistd::setgroups;
use nix::{
    fcntl::{AT_FDCWD, AtFlags},
    unistd::{Gid, Group, Uid, User, getuid, setgid, setuid},
};
use pyo3::{exceptions::PySystemExit, prelude::*, types::PyDict};
use tracing::{info, warn};

/// The unprivileged user the server runs as.
const AK_USER: &str = "authentik";
/// Mounted by deployments that let the worker manage outpost containers.
const DOCKER_SOCKET: &str = "/var/run/docker.sock";
/// Where Python's prometheus client keeps the metrics of each process.
const PROMETHEUS_MULTIPROC_DIR: &str = "PROMETHEUS_MULTIPROC_DIR";

#[derive(Debug, FromArgs, PartialEq)]
/// Run a Django management command.
#[argh(subcommand, name = "manage")]
pub(crate) struct Manage {
    /// the management command and its arguments
    #[argh(positional, greedy)]
    args: Vec<String>,
}

#[derive(Debug, FromArgs, PartialEq)]
/// Run the test suite.
#[argh(subcommand, name = "test-all")]
#[expect(
    clippy::empty_structs_with_brackets,
    reason = "argh doesn't support unit structs"
)]
pub(crate) struct TestAll {}

#[derive(Debug, FromArgs, PartialEq)]
/// Print the configuration, or the values of the given keys.
#[argh(subcommand, name = "dump_config")]
pub(crate) struct DumpConfig {
    /// the keys to print
    #[argh(positional, greedy)]
    keys: Vec<String>,
}

#[derive(Debug, FromArgs, PartialEq)]
/// Run bash.
#[argh(subcommand, name = "bash")]
pub(crate) struct Bash {
    /// the arguments for bash
    #[argh(positional, greedy)]
    args: Vec<String>,
}

#[derive(Debug, FromArgs, PartialEq)]
/// Run sh.
#[argh(subcommand, name = "sh")]
pub(crate) struct Sh {
    /// the arguments for sh
    #[argh(positional, greedy)]
    args: Vec<String>,
}

#[derive(Debug, FromArgs, PartialEq)]
/// Idle, so that a shell can be opened in the container.
#[argh(subcommand, name = "debug")]
#[expect(
    clippy::empty_structs_with_brackets,
    reason = "argh doesn't support unit structs"
)]
pub(crate) struct Debug {}

/// Where Python's prometheus client keeps the metrics of each process.
fn prometheus_dir() -> Result<PathBuf> {
    let dir = std::env::var_os(PROMETHEUS_MULTIPROC_DIR)
        .filter(|dir| !dir.is_empty())
        .map_or_else(
            || std::env::temp_dir().join("authentik_prometheus_tmp"),
            PathBuf::from,
        );
    fs::create_dir_all(&dir)?;
    Ok(dir)
}

/// Replace this process with `cmd`. Only returns when that fails.
fn exec(mut cmd: Command) -> Result<()> {
    let err = cmd.exec();
    Err(err).wrap_err_with(|| format!("failed to run {}", cmd.get_program().display()))
}

/// Run `cmd` and wait for it, failing when it fails.
fn run(cmd: &mut Command) -> Result<()> {
    let status = cmd
        .status()
        .wrap_err_with(|| format!("failed to run {}", cmd.get_program().display()))?;
    if !status.success() {
        return Err(eyre!(
            "{} exited with {status}",
            cmd.get_program().display()
        ));
    }
    Ok(())
}

/// Run `module` in this process, like `python -m module args...` would.
///
/// When Python raises `SystemExit`, the process exits with its code, as `python` would.
fn run_module(module: &str, args: &[String]) -> Result<()> {
    crate::python::initialize()?;
    let prometheus_dir = prometheus_dir()?;
    let cwd = std::env::current_dir()?;
    Python::attach(|py| {
        let result = (|| -> PyResult<()> {
            let sys = py.import("sys")?;
            // `python -m` puts the working directory first, so that `authentik` can be imported
            let path = sys.getattr("path")?;
            if !path.contains(cwd.as_os_str())? {
                path.call_method1("insert", (0_i32, cwd.as_os_str()))?;
            }
            let sys_argv: Vec<&str> = std::iter::once(module)
                .chain(args.iter().map(String::as_str))
                .collect();
            sys.setattr("argv", sys_argv)?;
            // Changing our own environment from Rust needs unsafe code, Python does it for us
            py.import("os")?
                .getattr("environ")?
                .set_item(PROMETHEUS_MULTIPROC_DIR, prometheus_dir.as_os_str())?;
            let kwargs = PyDict::new(py);
            kwargs.set_item("run_name", "__main__")?;
            kwargs.set_item("alter_sys", true)?;
            py.import("runpy")?
                .call_method("run_module", (module,), Some(&kwargs))?;
            Ok(())
        })();
        // We keep running after this, so don't leave output behind in Python's buffers
        for stream in ["stdout", "stderr"] {
            if let Ok(stream) = py.import("sys").and_then(|sys| sys.getattr(stream)) {
                let _ = stream.call_method0("flush");
            }
        }
        result.map_err(|err| {
            // Exits for `SystemExit`, prints the traceback otherwise
            err.print(py);
            eyre!("python module {module} failed")
        })
    })
}

/// Run `module` like [`run_module`], then exit like `python` would, running Python's exit handlers.
fn exec_module(module: &str, args: &[String]) -> Result<()> {
    run_module(module, args)?;
    Python::attach(|py| PySystemExit::new_err(0_i32).print(py));
    Err(eyre!("python did not exit after {module}"))
}

/// Install what `test-all` and `AUTHENTIK_DEBUGGER` need.
fn prepare_debug() -> Result<()> {
    // Only in the container, a development checkout has all of it already
    if !Path::new("/ak-root").is_dir() {
        return Ok(());
    }
    let venv = std::env::var_os("VENV_PATH").ok_or_else(|| eyre!("VENV_PATH is not set"))?;
    info!("installing the development dependencies");
    run(Command::new("apt-get").arg("update"))?;
    run(Command::new("apt-get")
        .args(["install", "-y", "--no-install-recommends"])
        .args([
            "krb5-kdc",
            "krb5-user",
            "krb5-admin-server",
            "libkrb5-dev",
            "gcc",
        ])
        .env("DEBIAN_FRONTEND", "noninteractive"))?;
    run(Command::new("uv")
        .args(["sync", "--active", "--locked"])
        .env("VIRTUAL_ENV", venv))?;
    // The test suite writes its report there after dropping to `authentik`, and can't create it
    let user = User::from_name(AK_USER)?.ok_or_else(|| eyre!("user {AK_USER} does not exist"))?;
    fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open("/unittest.xml")?;
    nix::unistd::chown("/unittest.xml", Some(user.uid), Some(user.gid))?;
    Ok(())
}

/// `chown -R`, skipping entries that already have the right owner.
fn chown_tree(path: &Path, uid: Uid, gid: Gid) -> Result<()> {
    if !path.exists() {
        return Ok(());
    }
    nix::unistd::chown(path, Some(uid), Some(gid))?;
    let mut stack = vec![path.to_path_buf()];
    while let Some(dir) = stack.pop() {
        let Ok(entries) = fs::read_dir(&dir) else {
            continue;
        };
        for entry in entries.flatten() {
            let child = entry.path();
            if entry.file_type().is_ok_and(|t| t.is_dir()) {
                stack.push(child.clone());
            }
            let Ok(meta) = fs::symlink_metadata(&child) else {
                continue;
            };
            if meta.uid() == uid.as_raw() && meta.gid() == gid.as_raw() {
                continue;
            }
            if let Err(err) = nix::unistd::fchownat(
                AT_FDCWD,
                &child,
                Some(uid),
                Some(gid),
                AtFlags::AT_SYMLINK_NOFOLLOW,
            ) {
                warn!(path = %child.display(), %err, "could not change owner");
            }
        }
    }
    Ok(())
}

fn add_mode(path: &Path, bits: u32) -> Result<()> {
    if !path.is_dir() {
        return Ok(());
    }
    let mut perms = fs::metadata(path)?.permissions();
    perms.set_mode(perms.mode() | bits);
    fs::set_permissions(path, perms)?;
    Ok(())
}

/// The gid that owns a mounted docker socket, if there is one.
fn docker_socket_gid() -> Option<Gid> {
    fs::metadata(DOCKER_SOCKET)
        .ok()
        .map(|meta| Gid::from_raw(meta.gid()))
}

/// Fix up ownership while still root, then switch to `authentik`. Returns its home directory.
fn become_authentik(prometheus_dir: &Path) -> Result<PathBuf> {
    let user = User::from_name(AK_USER)?.ok_or_else(|| eyre!("user {AK_USER} does not exist"))?;
    let mut groups = vec![user.gid];

    if let Some(gid) = docker_socket_gid()
        && !groups.contains(&gid)
    {
        // setgroups takes the numeric gid directly
        let name = Group::from_gid(gid)
            .ok()
            .flatten()
            .map_or_else(|| "unnamed".to_owned(), |g| g.name);
        info!(
            gid = gid.as_raw(),
            group = name,
            "granting access to the docker socket"
        );
        groups.push(gid);
    }

    for path in [Path::new("/data"), Path::new("/certs"), prometheus_dir] {
        chown_tree(path, user.uid, user.gid)
            .wrap_err_with(|| format!("failed to change owner of {}", path.display()))?;
    }
    // Mirrors the old `chmod ug+rwx /data` and `chmod ug+rx /certs`
    add_mode(Path::new("/data"), 0o770)?;
    // 'certs' deliberately gets no owner write bit
    add_mode(Path::new("/certs"), 0o550)?;

    #[cfg(target_os = "linux")]
    setgroups(&groups)?;
    setgid(user.gid)?;
    setuid(user.uid)?;
    // Still being root would make `boot` loop
    if getuid() != user.uid || getuid().is_root() {
        return Err(eyre!("failed to drop privileges to {AK_USER}"));
    }
    Ok(user.dir)
}

fn wait_for_db() -> Result<()> {
    run_module("lifecycle.wait_for_db", &[])?;
    info!("bootstrap completed");
    Ok(())
}

fn run_migrations() -> Result<()> {
    run_module("lifecycle.migrate", &[])?;
    info!("migrations completed");
    Ok(())
}

/// Get the process ready to run the server or the worker.
pub(crate) fn bootstrap() -> Result<()> {
    let prometheus_dir = prometheus_dir()?;
    let mut env = Vec::new();
    if std::env::var_os(PROMETHEUS_MULTIPROC_DIR).as_deref() != Some(prometheus_dir.as_os_str()) {
        env.push((PROMETHEUS_MULTIPROC_DIR, prometheus_dir.clone()));
    }
    if getuid().is_root() {
        config::init()?;
        if config::get().debugger {
            prepare_debug()?;
        }
        env.push(("HOME", become_authentik(&prometheus_dir)?));
    }
    // Changing our own environment needs unsafe code, so exec ourselves with the new one
    if !env.is_empty() {
        let mut cmd = Command::new(std::env::current_exe()?);
        cmd.args(std::env::args_os().skip(1)).envs(env);
        return exec(cmd);
    }
    wait_for_db()?;
    run_migrations()
}

pub(crate) fn manage(args: &Manage) -> Result<()> {
    // manage.py waits for the database itself
    exec_module("manage", &args.args)
}

pub(crate) fn test_all() -> Result<()> {
    let prometheus_dir = prometheus_dir()?;
    if getuid().is_root() {
        prepare_debug()?;
        let home = become_authentik(&prometheus_dir)?;
        // Changing our own environment needs unsafe code, so exec ourselves with the new one
        let mut cmd = Command::new(std::env::current_exe()?);
        cmd.args(std::env::args_os().skip(1)).env("HOME", home);
        return exec(cmd);
    }
    // manage.py waits for the database itself
    exec_module("manage", &["test".to_owned(), "authentik".to_owned()])
}

pub(crate) fn dump_config(args: &DumpConfig) -> Result<()> {
    exec_module("authentik.lib.config", &args.keys)
}

fn shell(program: &str, args: &[String]) -> Result<()> {
    let mut cmd = Command::new(program);
    cmd.args(args)
        .env(PROMETHEUS_MULTIPROC_DIR, prometheus_dir()?);
    exec(cmd)
}

pub(crate) fn bash(args: &Bash) -> Result<()> {
    shell("bash", &args.args)
}

pub(crate) fn sh(args: &Sh) -> Result<()> {
    shell("sh", &args.args)
}

pub(crate) fn idle() -> ! {
    loop {
        std::thread::sleep(Duration::from_hours(1));
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // `lifecycle/ak.py` puts a `--` in front of these, so that argh keeps what follows as it is
    #[test]
    fn arguments_after_the_separator_are_kept() {
        for args in [
            &["--help"][..],
            &["help"],
            &["shell", "-c", "print(1)"],
            &["migrate", "--", "--fake"],
        ] {
            let argv: Vec<&str> = std::iter::once("--").chain(args.iter().copied()).collect();
            let manage = Manage::from_args(&["manage"], &argv).expect("failed to parse");
            assert_eq!(manage.args, args);
        }
    }

    #[test]
    fn shell_flags_are_kept() {
        let bash = Bash::from_args(&["bash"], &["--", "-c", "echo hi"]).expect("failed to parse");
        assert_eq!(bash.args, ["-c", "echo hi"]);
    }
}
