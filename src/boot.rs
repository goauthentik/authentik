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

use argh::FromArgs;
use eyre::{Result, WrapErr as _, eyre};
use nix::{
    fcntl::{AT_FDCWD, AtFlags},
    unistd::{Gid, Group, Uid, User, getuid, setgid, setgroups, setuid},
};
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
    let status = Command::new("python")
        .args(["-m", "lifecycle.wait_for_db"])
        .status()?;
    if !status.success() {
        return Err(eyre!("wait_for_db exited with {status}"));
    }
    info!("bootstrap completed");
    Ok(())
}

/// Get the process ready to run the server or the worker.
pub(crate) fn boot() -> Result<()> {
    let prometheus_dir = prometheus_dir()?;
    let mut env = Vec::new();
    if std::env::var_os(PROMETHEUS_MULTIPROC_DIR).as_deref() != Some(prometheus_dir.as_os_str()) {
        env.push((PROMETHEUS_MULTIPROC_DIR, prometheus_dir.clone()));
    }
    if getuid().is_root() {
        env.push(("HOME", become_authentik(&prometheus_dir)?));
    }
    // Changing our own environment needs unsafe code, so exec ourselves with the new one
    if !env.is_empty() {
        let mut cmd = Command::new(std::env::current_exe()?);
        cmd.args(std::env::args_os().skip(1)).envs(env);
        return exec(cmd);
    }
    wait_for_db()
}

pub(crate) fn manage(args: &Manage) -> Result<()> {
    // manage.py waits for the database itself
    let mut cmd = Command::new("python");
    cmd.args(["-m", "manage"])
        .args(&args.args)
        .env(PROMETHEUS_MULTIPROC_DIR, prometheus_dir()?);
    exec(cmd)
}

pub(crate) fn test_all() -> Result<()> {
    let prometheus_dir = prometheus_dir()?;
    // manage.py waits for the database itself
    let mut cmd = Command::new("python");
    cmd.args(["-m", "manage", "test", "authentik"])
        .env(PROMETHEUS_MULTIPROC_DIR, &prometheus_dir);
    if getuid().is_root() {
        // The bash entrypoint opened up /root first, because the suite writes there
        add_mode(Path::new("/root"), 0o777)?;
        cmd.env("HOME", become_authentik(&prometheus_dir)?);
    }
    exec(cmd)
}

pub(crate) fn dump_config(args: &DumpConfig) -> Result<()> {
    let mut cmd = Command::new("python");
    cmd.args(["-m", "authentik.lib.config"])
        .args(&args.keys)
        .env(PROMETHEUS_MULTIPROC_DIR, prometheus_dir()?);
    exec(cmd)
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
