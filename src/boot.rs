//! Container entrypoint

use std::{
    collections::BTreeMap,
    ffi::{CString, OsStr, OsString},
    fs,
    os::unix::{
        ffi::OsStringExt as _,
        fs::{MetadataExt as _, PermissionsExt as _},
    },
    path::{Path, PathBuf},
    process::Command,
};

use argh::FromArgs;
use eyre::{Report, Result, WrapErr as _, eyre};
use nix::{
    fcntl::{AT_FDCWD, AtFlags},
    unistd::{Gid, Group, Uid, User, execve, execvpe, getuid, setgid, setgroups, setuid},
};
use tracing::{info, warn};

/// The unprivileged user the server runs as.
const AK_USER: &str = "authentik";
/// Mounted by deployments that let the worker manage outpost containers.
const DOCKER_SOCKET: &str = "/var/run/docker.sock";
/// Where the Dockerfile puts the compiled binary.
const AUTHENTIK_BIN: &str = "/bin/authentik";
/// Subcommands this binary implements itself.
const NATIVE_COMMANDS: [&str; 4] = ["server", "worker", "allinone", "healthcheck"];

#[derive(Debug, FromArgs, PartialEq)]
/// Prepare the container, drop privileges and exec the real process.
#[argh(subcommand, name = "boot")]
pub(crate) struct Cli {
    /// the ak subcommand and its arguments
    #[argh(positional, greedy)]
    args: Vec<String>,
}

fn venv_python() -> PathBuf {
    let venv = std::env::var("VENV_PATH").unwrap_or_else(|_| "/ak-root/.venv".to_owned());
    PathBuf::from(venv).join("bin/python")
}

fn tmpdir() -> PathBuf {
    PathBuf::from(std::env::var("TMPDIR").unwrap_or_else(|_| "/tmp".to_owned()))
}

/// True when this binary was invoked through the `/lifecycle/ak` symlink.
pub(crate) fn invoked_as_ak(argv0: &str) -> bool {
    Path::new(argv0).file_name() == Some(OsStr::new("ak"))
}

/// Map an `ak` invocation onto the argv of the program to exec.
fn resolve_target(args: &[String]) -> Vec<String> {
    let python = venv_python().to_string_lossy().into_owned();
    match args.first().map(String::as_str) {
        Some(cmd) if NATIVE_COMMANDS.contains(&cmd) => {
            let mut target = vec![AUTHENTIK_BIN.to_owned()];
            target.extend_from_slice(args);
            target
        }
        Some("manage") => {
            let mut target = vec![python, "-m".to_owned(), "manage".to_owned()];
            target.extend_from_slice(&args[1..]);
            target
        }
        _ => {
            let mut target = vec![python, "-m".to_owned(), "manage".to_owned()];
            target.extend_from_slice(args);
            target
        }
    }
}

/// `execve` replaces the environment, so the current one is a snapshot and the overrides are
/// applied to the copy
fn exec(argv: &[String], extra_env: &[(&str, String)]) -> Result<()> {
    let cargv = argv
        .iter()
        .map(|a| CString::new(a.as_str()))
        .collect::<Result<Vec<_>, _>>()?;
    let program = CString::new(argv[0].as_str())?;

    let mut env: BTreeMap<OsString, OsString> = std::env::vars_os().collect();
    for (key, value) in extra_env {
        env.insert(OsString::from(*key), OsString::from(value));
    }
    let cenv = env
        .into_iter()
        .map(|(key, value)| {
            let mut pair = key;
            pair.push("=");
            pair.push(value);
            CString::new(pair.into_vec())
        })
        .collect::<Result<Vec<_>, _>>()?;

    if argv[0].contains('/') {
        execve(&program, &cargv, &cenv)?;
    } else {
        execvpe(&program, &cargv, &cenv)?;
    }
    unreachable!("exec returned without an error")
}

/// The shell the debug image has. The production image has none
fn find_shell() -> Option<PathBuf> {
    ["/bin/bash", "/usr/bin/bash", "/bin/sh", "/usr/bin/sh"]
        .into_iter()
        .map(PathBuf::from)
        .find(|shell| shell.is_file())
}

fn no_shell_error(command: &str) -> Report {
    eyre!(
        "'{command}' is not available in the production image, which ships no shell. Use the \
         server-debug image: it is the same build with apt, a shell and the dev dependency group."
    )
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

/// Fix up ownership while still root, then exec the target as `authentik`.
fn run_as_authentik(args: &[String], prometheus_dir: &str) -> Result<()> {
    let target = resolve_target(args);
    let mut env = vec![("PROMETHEUS_MULTIPROC_DIR", prometheus_dir.to_owned())];

    if !getuid().is_root() {
        info!("not running as root, disabling permission fixes");
        return exec(&target, &env);
    }

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

    for path in ["/data", "/certs", prometheus_dir] {
        chown_tree(Path::new(path), user.uid, user.gid)
            .wrap_err_with(|| format!("failed to change owner of {path}"))?;
    }
    // Mirrors the old `chmod ug+rwx /data` and `chmod ug+rx /certs`
    add_mode(Path::new("/data"), 0o770)?;
    // 'certs' deliberately gets no owner write bit
    add_mode(Path::new("/certs"), 0o550)?;

    env.push(("HOME", user.dir.to_string_lossy().into_owned()));

    setgroups(&groups)?;
    setgid(user.gid)?;
    setuid(user.uid)?;
    if getuid() != user.uid {
        return Err(eyre!("failed to drop privileges to {AK_USER}"));
    }

    exec(&target, &env)
}

fn wait_for_db(prometheus_dir: &str) -> Result<()> {
    let status = Command::new(venv_python())
        .args(["-m", "lifecycle.wait_for_db"])
        .env("PROMETHEUS_MULTIPROC_DIR", prometheus_dir)
        .status()?;
    if !status.success() {
        return Err(eyre!("wait_for_db exited with {status}"));
    }
    info!("bootstrap completed");
    Ok(())
}

pub(crate) fn run(cli: &Cli) -> Result<()> {
    // Keep what the deployment set, otherwise fall back to a directory under
    // TMPDIR. Every exec below carries this to the child explicitly.
    let prometheus_dir = match std::env::var("PROMETHEUS_MULTIPROC_DIR") {
        Ok(dir) if !dir.is_empty() => dir,
        _ => tmpdir()
            .join("authentik_prometheus_tmp")
            .to_string_lossy()
            .into_owned(),
    };
    fs::create_dir_all(&prometheus_dir)?;
    let env = [("PROMETHEUS_MULTIPROC_DIR", prometheus_dir.clone())];

    let args = &cli.args;
    let Some(command) = args.first().map(String::as_str) else {
        return Err(eyre!(
            "usage: ak <server|worker|allinone|healthcheck|dump_config|MANAGE_COMMAND>"
        ));
    };

    match command {
        // These need a shell, which only the -debug image ships.
        "bash" | "sh" => {
            let Some(shell) = find_shell() else {
                return Err(no_shell_error(command));
            };
            let mut target = vec![shell.to_string_lossy().into_owned()];
            target.extend_from_slice(&args[1..]);
            exec(&target, &env)
        }
        "test-all" => {
            if find_shell().is_none() {
                return Err(no_shell_error(command));
            }
            // The bash entrypoint opened up /root first, because the suite
            // writes there, then ran `manage test authentik`.
            if getuid().is_root() {
                add_mode(Path::new("/root"), 0o777)?;
            }
            wait_for_db(&prometheus_dir)?;
            let target = ["manage", "test", "authentik"].map(str::to_owned).to_vec();
            run_as_authentik(&target, &prometheus_dir)
        }
        "dump_config" => {
            let python = venv_python().to_string_lossy().into_owned();
            let mut target = vec![python, "-m".to_owned(), "authentik.lib.config".to_owned()];
            target.extend_from_slice(&args[1..]);
            exec(&target, &env)
        }
        #[expect(
            clippy::infinite_loop,
            reason = "the debug entrypoint idles so a user can exec into the container"
        )]
        "debug" => loop {
            std::thread::sleep(std::time::Duration::from_hours(1));
        },
        "allinone" | "server" | "worker" => {
            wait_for_db(&prometheus_dir)?;
            run_as_authentik(args, &prometheus_dir)
        }
        "healthcheck" => {
            // `authentik healthcheck` takes the mode as a positional argument.
            // The server writes it to $TMPDIR/authentik-mode on startup.
            let mut target = args.clone();
            if target.len() == 1 {
                match fs::read_to_string(tmpdir().join("authentik-mode")) {
                    Ok(mode) if !mode.trim().is_empty() => target.push(mode.trim().to_owned()),
                    _ => warn!(
                        "no mode file yet, the healthcheck will fail until the server writes one"
                    ),
                }
            }
            run_as_authentik(&target, &prometheus_dir)
        }
        _ => {
            wait_for_db(&prometheus_dir)?;
            let python = venv_python().to_string_lossy().into_owned();
            let mut target = vec![python, "-m".to_owned(), "manage".to_owned()];
            target.extend_from_slice(args);
            exec(&target, &env)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn owned(args: &[&str]) -> Vec<String> {
        args.iter().map(|a| (*a).to_owned()).collect()
    }

    #[test]
    fn native_commands_go_to_the_binary() {
        for cmd in NATIVE_COMMANDS {
            let argv = resolve_target(&owned(&[cmd]));
            assert_eq!(argv[0], AUTHENTIK_BIN);
            assert_eq!(argv[1], cmd);
        }
    }

    #[test]
    fn healthcheck_keeps_its_mode_argument() {
        let argv = resolve_target(&owned(&["healthcheck", "worker"]));
        assert_eq!(argv, vec![AUTHENTIK_BIN, "healthcheck", "worker"]);
    }

    #[test]
    fn management_commands_go_to_django() {
        let argv = resolve_target(&owned(&["test_email", "a@b.c"]));
        assert!(argv[0].ends_with("/bin/python"));
        assert_eq!(&argv[1..], ["-m", "manage", "test_email", "a@b.c"]);
    }

    #[test]
    fn an_explicit_manage_prefix_is_not_repeated() {
        let argv = resolve_target(&owned(&["manage", "migrate"]));
        assert_eq!(&argv[1..], ["-m", "manage", "migrate"]);
    }

    #[test]
    fn flags_survive_the_dispatch() {
        let argv = resolve_target(&owned(&["shell", "-c", "print(1)"]));
        assert_eq!(&argv[1..], ["-m", "manage", "shell", "-c", "print(1)"]);
    }

    #[test]
    fn the_ak_symlink_is_recognized() {
        assert!(invoked_as_ak("/lifecycle/ak"));
        assert!(invoked_as_ak("ak"));
        assert!(!invoked_as_ak("/bin/authentik"));
        assert!(!invoked_as_ak("authentik"));
    }
}
