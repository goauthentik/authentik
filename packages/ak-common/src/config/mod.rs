use std::{
    collections::BTreeSet,
    env,
    fs::{self, read_to_string},
    mem,
    path::{self, Path, PathBuf},
    sync::{Arc, Mutex, OnceLock, PoisonError},
};

use arc_swap::ArcSwap;
use eyre::Result;
use notify::{RecommendedWatcher, Watcher, event::EventKind};
use serde_json::{Map, Value};
use tokio::{sync::mpsc, task::spawn_blocking};
use tracing::{debug, error, info, warn};
use url::Url;

pub mod schema;
pub use schema::Config;

use crate::{
    arbiter::{Arbiter, Event, Tasks},
    config::schema::KEYS_TO_PARSE_AS_LIST,
};

static DEFAULT_CONFIG: &str = include_str!("../../../../authentik/lib/default.yml");
static CONFIG_MANAGER: OnceLock<ConfigManager> = OnceLock::new();

/// List of paths from where to read YAML configuration.
fn config_paths() -> Vec<PathBuf> {
    let mut config_paths = vec![
        PathBuf::from("/etc/authentik/config.yml"),
        PathBuf::from(""),
    ];
    if let Ok(workspace) = env::var("WORKSPACE_DIR") {
        let _ = env::set_current_dir(workspace);
    }

    if let Ok(paths) = glob::glob("/etc/authentik/config.d/*.yml") {
        config_paths.extend(paths.filter_map(Result::ok));
    }

    let environment = env::var("AUTHENTIK_ENV").unwrap_or_else(|_| "local".to_owned());

    let mut computed_paths = Vec::new();

    for path in config_paths {
        if let Ok(metadata) = fs::metadata(&path) {
            if !metadata.is_dir() {
                computed_paths.push(path);
            }
        } else {
            let env_paths = vec![
                path.join(format!("{environment}.yml")),
                path.join(format!("{environment}.env.yml")),
            ];
            for env_path in env_paths {
                if let Ok(metadata) = fs::metadata(&env_path)
                    && !metadata.is_dir()
                {
                    computed_paths.push(env_path);
                }
            }
        }
    }

    computed_paths
}

impl Config {
    /// Load the configuration from files and environment into a [`Value`], allowing for extra
    /// processing later.
    fn load_raw(config_paths: &[PathBuf], overrides: Option<Value>) -> Result<Value> {
        let mut builder = config_rs::Config::builder().add_source(config_rs::File::from_str(
            DEFAULT_CONFIG,
            config_rs::FileFormat::Yaml,
        ));
        for path in config_paths {
            builder = builder.add_source(
                config_rs::File::from(path.as_path()).format(config_rs::FileFormat::Yaml),
            );
        }
        let mut env_source = config_rs::Environment::with_prefix("AUTHENTIK")
            .prefix_separator("_")
            .separator("__")
            .try_parsing(true)
            .list_separator(",");
        for key in KEYS_TO_PARSE_AS_LIST {
            env_source = env_source.with_list_parse_key(key);
        }
        builder = builder.add_source(env_source);
        if let Some(overrides) = overrides {
            builder = builder.add_source(config_rs::File::from_str(
                &overrides.to_string(),
                config_rs::FileFormat::Json,
            ));
        }
        let config = builder.build()?;
        let raw = config.try_deserialize::<Value>()?;
        Ok(raw)
    }

    /// Expand a value if it matches an env:// or file:// protocol.
    ///
    /// If expanded from a file, returns the file path for it to be watched later.
    fn expand_value(value: &str) -> (String, Option<PathBuf>) {
        let value = value.trim();
        if let Ok(uri) = Url::parse(value) {
            let fallback = uri.query().unwrap_or("").to_owned();
            match uri.scheme() {
                "file" => {
                    let path = uri.path();
                    match read_to_string(path).map(|s| s.trim().to_owned()) {
                        Ok(value) => return (value, Some(PathBuf::from(path))),
                        Err(err) => {
                            error!(
                                ?err,
                                "failed to read config value from '{path}', using fallback"
                            );
                            return (fallback, Some(PathBuf::from(path)));
                        }
                    }
                }
                "env" => {
                    if let Some(var) = uri.host_str() {
                        if let Ok(value) = env::var(var) {
                            return (value, None);
                        }
                        return (fallback, None);
                    }
                }
                _ => {}
            }
        }

        (value.to_owned(), None)
    }

    /// Expand the configuration for env:// and file:// values.
    ///
    /// Returns the expanded configuration and a list of file paths for which to watch changes.
    fn expand(mut raw: Value) -> (Value, Vec<PathBuf>) {
        let mut file_paths = Vec::new();
        let value = match &mut raw {
            Value::String(s) => {
                let (v, path) = Self::expand_value(s);
                if let Some(path) = path {
                    file_paths.push(path);
                }
                Value::String(v)
            }
            Value::Array(arr) => {
                let mut res = Vec::with_capacity(arr.len());
                for v in arr {
                    let (expanded, paths) = Self::expand(v.clone());
                    file_paths.extend(paths);
                    res.push(expanded);
                }
                Value::Array(res)
            }
            Value::Object(map) => {
                let mut res = Map::with_capacity(map.len());
                for (k, v) in map {
                    let (expanded, paths) = Self::expand(v.clone());
                    file_paths.extend(paths);
                    res.insert(k.clone(), expanded);
                }
                Value::Object(res)
            }
            _ => raw,
        };
        (value, file_paths)
    }

    /// Load the configuration.
    fn load(config_paths: &[PathBuf], overrides: Option<Value>) -> Result<(Self, Vec<PathBuf>)> {
        let raw = Self::load_raw(config_paths, overrides)?;
        let (expanded, file_paths) = Self::expand(raw);
        let config: Self = serde_json::from_value(expanded)?;
        Ok((config, file_paths))
    }
}

/// Manager of the config. Handles reloading when changed on disk.
struct ConfigManager {
    config: ArcSwap<Config>,
    config_paths: Vec<PathBuf>,
    watch_paths: Vec<PathBuf>,
}

/// Initialize the configuration. It relies on a global [`OnceLock`] and must be called before
/// other methods are called.
pub fn init() -> Result<()> {
    info!("loading config");
    let config_paths = config_paths();
    init_with_paths(config_paths)?;
    info!("config loaded");
    Ok(())
}

/// Initialize the configuration from a list of specific paths to read if from.
fn init_with_paths(config_paths: Vec<PathBuf>) -> Result<()> {
    let (config, mut other_paths) = Config::load(&config_paths, None)?;
    let mut watch_paths = config_paths.clone();
    watch_paths.append(&mut other_paths);
    let manager = ConfigManager {
        config: ArcSwap::from_pointee(config),
        config_paths,
        watch_paths,
    };
    CONFIG_MANAGER.get_or_init(|| manager);
    Ok(())
}

/// A watched file, with the file its path resolved to when last checked.
struct WatchedFile {
    path: PathBuf,
    resolved: Option<PathBuf>,
}

/// Decides whether a filesystem event changed one of the watched files: an event names it while
/// it exists, or it now resolves to a different file or to none, as when the kubelet repoints
/// `..data` or the file is deleted.
struct ChangeDetector {
    files: Vec<WatchedFile>,
}

impl ChangeDetector {
    fn new(paths: &[PathBuf]) -> Self {
        let files = paths
            .iter()
            .map(|path| WatchedFile {
                path: path.clone(),
                resolved: fs::canonicalize(path).ok(),
            })
            .collect();
        Self { files }
    }

    fn is_change(&mut self, event: &notify::Event) -> bool {
        // Reading the files must not trigger a reload.
        if matches!(event.kind, EventKind::Access(_)) {
            return false;
        }
        // Events were dropped, so anything may have changed.
        let mut changed = event.need_rescan();
        for file in &mut self.files {
            let current = fs::canonicalize(&file.path).ok();
            // Some platforms, macOS included, report events by the real path of the file.
            let named = event
                .paths
                .iter()
                .any(|p| *p == file.path || current.as_ref() == Some(p));
            // A file renamed away or deleted is reloaded so that its fallback applies, and again
            // once it exists, but events about it in between change nothing.
            if current != file.resolved || (named && current.is_some()) {
                changed = true;
            }
            file.resolved = current;
        }
        changed
    }
}

/// Create a watcher that reports changes detected by `detector` through `tx`.
fn new_watcher(
    detector: &Arc<Mutex<ChangeDetector>>,
    tx: &mpsc::Sender<()>,
) -> notify::Result<RecommendedWatcher> {
    let detector = Arc::clone(detector);
    let tx = tx.clone();
    RecommendedWatcher::new(
        move |res: notify::Result<notify::Event>| {
            let Ok(event) = res else {
                return;
            };
            let changed = detector
                .lock()
                .unwrap_or_else(PoisonError::into_inner)
                .is_change(&event);
            if changed {
                let _ = tx.try_send(());
            }
        },
        notify::Config::default(),
    )
}

/// The outcome of watching a path.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum WatchState {
    Watched,
    /// There is nothing to watch.
    Missing,
    Failed,
}

/// Watch each of `paths`, returning the outcome for each of them.
///
/// A failure must not stop authentik: a file may not exist yet and a directory may only be
/// traversable. Running out of inotify watches leaves changes undetected.
fn watch_all<W: Watcher>(
    watcher: &mut W,
    paths: &[PathBuf],
    after_change: bool,
) -> Vec<WatchState> {
    paths
        .iter()
        .map(
            |path| match watcher.watch(path, notify::RecursiveMode::NonRecursive) {
                Ok(()) => WatchState::Watched,
                Err(err) => {
                    let state = if matches!(err.kind, notify::ErrorKind::PathNotFound) {
                        WatchState::Missing
                    } else {
                        WatchState::Failed
                    };
                    if matches!(err.kind, notify::ErrorKind::MaxFilesWatch) {
                        error!(?err, path = %path.display(), "failed to watch for config changes");
                    } else if after_change {
                        debug!(?err, path = %path.display(), "failed to watch for config changes");
                    } else {
                        warn!(?err, path = %path.display(), "failed to watch for config changes");
                    }
                    state
                }
            },
        )
        .collect()
}

/// Replace `current` with `replacement` unless that loses a watch of `current`, whose state for
/// each of `paths` is tracked in `states`.
///
/// The replacement is set up before the current watcher is dropped. A path that no longer exists
/// has no watch to lose if the replacement watches its directory; otherwise only the current watch
/// notices it coming back, should the file have been renamed away.
fn hand_over<W: Watcher>(
    current: &mut W,
    states: &mut [WatchState],
    replacement: notify::Result<W>,
    paths: &[PathBuf],
) {
    match replacement {
        Ok(mut replacement) => {
            let new_states = watch_all(&mut replacement, paths, true);
            let dir_watched = |path: &Path| {
                path.parent().is_some_and(|dir| {
                    paths
                        .iter()
                        .zip(&new_states)
                        .any(|(p, state)| p == dir && *state == WatchState::Watched)
                })
            };
            let loses_watch =
                paths
                    .iter()
                    .zip(states.iter().zip(&new_states))
                    .any(|(path, (old, new))| {
                        *old == WatchState::Watched
                            && match new {
                                WatchState::Watched => false,
                                WatchState::Missing => !dir_watched(path),
                                WatchState::Failed => true,
                            }
                    });
            if !loses_watch {
                drop(mem::replace(current, replacement));
                states.copy_from_slice(&new_states);
                return;
            }
            warn!(
                "a new config file watcher failed to watch what the current one does, reusing the \
                 current one"
            );
        }
        Err(err) => {
            warn!(
                ?err,
                "failed to create a new config file watcher, reusing the current one"
            );
        }
    }
}

/// Watch for configuration changes, reload the configuration in memory and send events.
///
/// [`init`] must be called before this is used.
async fn watch_config(arbiter: Arbiter) -> Result<()> {
    let watch_paths: Vec<PathBuf> = CONFIG_MANAGER
        .get()
        .expect("failed to get config, has it been initialized?")
        .watch_paths
        .iter()
        .map(|path| path::absolute(path).unwrap_or_else(|_| path.clone()))
        .collect();
    // A watch is lost along with the file when the file is replaced rather than written to, as
    // editors do when saving atomically and the kubelet does when updating a mounted `Secret` or
    // `ConfigMap`. A new watcher is therefore created after each change, and the directories are
    // watched to catch files that have no watch to lose.
    let watch_dirs: BTreeSet<PathBuf> = watch_paths
        .iter()
        .filter_map(|path| path.parent().map(Path::to_path_buf))
        .collect();
    let watch_targets: Vec<PathBuf> = watch_paths.iter().chain(&watch_dirs).cloned().collect();

    // A single slot: a change arriving while a reload is already pending needs no second one.
    let (tx, mut rx) = mpsc::channel(1);
    let detector = Arc::new(Mutex::new(ChangeDetector::new(&watch_paths)));
    let mut watcher = new_watcher(&detector, &tx)?;
    let mut states = watch_all(&mut watcher, &watch_targets, false);

    let _ = arbiter.send_event(Event::ConfigChanged);
    info!(paths = ?watch_paths, dirs = ?watch_dirs, "config file watcher started");

    loop {
        tokio::select! {
            res = rx.recv() => {
                info!("a configuration file changed, reloading config");
                if res.is_none() {
                    break;
                }
                hand_over(&mut watcher, &mut states, new_watcher(&detector, &tx), &watch_targets);
                let manager = CONFIG_MANAGER.get().expect("failed to get config, has it been initialized?");
                match spawn_blocking(|| Config::load(&manager.config_paths, None)).await? {
                    Ok((new_config, _)) => {
                        info!("configuration reloaded");
                        manager.config.store(Arc::new(new_config));
                        if let Err(err) = arbiter.send_event(Event::ConfigChanged) {
                            warn!(?err, "failed to notify of config change, aborting");
                            break;
                        }
                    }
                    Err(err) => {
                        warn!(?err, "failed to reload config, continuing with previous config");
                    }
                }
            },
            () = arbiter.shutdown() => break,
        }
    }

    info!("stopping config file watcher");

    Ok(())
}

/// Start the configuration watcher.
///
/// [`init`] must be called before this is used.
pub fn start(tasks: &mut Tasks) -> Result<()> {
    info!("starting config file watcher");
    let arbiter = tasks.arbiter();
    tasks
        .build_task()
        .name(&format!("{}::watch_config", module_path!()))
        .spawn(watch_config(arbiter))?;
    Ok(())
}

/// Get the currently stored configuration.
///
/// [`init`] must be called before this is used.
pub fn get() -> arc_swap::Guard<Arc<Config>> {
    let manager = CONFIG_MANAGER
        .get()
        .expect("failed to get config, has it been initialized?");
    manager.config.load()
}

/// Test helper to set arbitrary config values.
#[cfg(test)]
pub fn set(value: Value) -> Result<()> {
    let manager = CONFIG_MANAGER
        .get()
        .expect("failed to get config, has it been initialized?");
    let (new_config, _) = Config::load(&manager.config_paths, Some(value))?;
    manager.config.store(Arc::new(new_config));
    Ok(())
}

#[cfg(test)]
mod tests {
    use std::{
        env,
        fs::{self, File, Permissions},
        io::{self, Write as _},
        os::unix::fs::{PermissionsExt as _, symlink},
        path::{Path, PathBuf},
        time::Duration,
    };

    use notify::event::{
        AccessKind, CreateKind, DataChange, EventKind, Flag, MetadataKind, ModifyKind, RemoveKind,
        RenameMode,
    };
    use serde_json::json;
    use tempfile::tempdir;
    use tokio::{
        sync::broadcast,
        time::{sleep, timeout},
    };

    use super::WatchState;
    use crate::arbiter::{Event, Tasks};

    #[test]
    fn default_config() {
        let (config, _) = super::Config::load(&[], None).expect("default config doesn't load");
        assert_eq!(config.secret_key, "");
    }

    #[test]
    fn config_paths() {
        let temp_dir = tempdir().expect("failed to create temp dir");
        for f in &[
            "local.env.yml",
            "local.env.yaml",
            "test_config_paths.yml",
            "test_config_paths.env.yml",
            "test_config_paths.env.yaml",
        ] {
            File::create(temp_dir.path().join(f)).expect("failed to create file");
        }
        #[expect(unsafe_code, reason = "testing")]
        // SAFETY: testing
        unsafe {
            env::set_var("WORKSPACE_DIR", temp_dir.path());
            env::set_var("AUTHENTIK_ENV", "test_config_paths");
        }

        let paths = super::config_paths();

        assert_eq!(
            &paths,
            &[
                PathBuf::from("test_config_paths.yml"),
                PathBuf::from("test_config_paths.env.yml"),
            ]
        );
    }

    #[test]
    fn expand() {
        let temp_dir = tempdir().expect("failed to create temp dir");

        let secret_key_path = temp_dir.path().join("secret_key");
        let mut secret_key_file = File::create(&secret_key_path).expect("failed to create file");
        write!(secret_key_file, "my_secret_key").expect("failed to write to file");

        let config_file_path = temp_dir.path().join("config");
        let mut config_file = File::create(&config_file_path).expect("failed to create file");
        writeln!(
            config_file,
            "secret_key: file://{}\npostgresql:\n  password: env://TEST_CONFIG_POSTGRES_PASS",
            secret_key_path.display()
        )
        .expect("failed to write to file");

        #[expect(unsafe_code, reason = "testing")]
        // SAFETY: testing
        unsafe {
            env::set_var("TEST_CONFIG_POSTGRES_PASS", "my_postgres_pass");
        }

        let (config, config_paths) =
            super::Config::load(&[config_file_path], None).expect("failed to load config");

        assert_eq!(config.secret_key, "my_secret_key");
        assert_eq!(config.postgresql.password, "my_postgres_pass");
        assert_eq!(config_paths, &[secret_key_path]);
    }

    #[test]
    fn expand_typed() {
        let temp_dir = tempdir().expect("failed to create temp dir");

        // A numeric value destined for an integer field (postgresql.port: u16) must be coerced
        // from the string a file:// reference resolves to.
        let port_path = temp_dir.path().join("port");
        let mut port_file = File::create(&port_path).expect("failed to create file");
        write!(port_file, "5432").expect("failed to write to file");
        drop(port_file);

        // A numeric-looking value destined for a string field (postgresql.password) must stay a
        // string and never be coerced into a number.
        let password_path = temp_dir.path().join("password");
        let mut password_file = File::create(&password_path).expect("failed to create file");
        write!(password_file, "12345").expect("failed to write to file");
        drop(password_file);

        let config_file_path = temp_dir.path().join("config");
        let mut config_file = File::create(&config_file_path).expect("failed to create file");
        writeln!(
            config_file,
            "postgresql:\n  port: file://{}\n  password: file://{}",
            port_path.display(),
            password_path.display()
        )
        .expect("failed to write to file");
        drop(config_file);

        let (config, _) =
            super::Config::load(&[config_file_path], None).expect("failed to load config");

        assert_eq!(config.postgresql.port, 5432);
        assert_eq!(config.postgresql.password, "12345");
    }

    #[test]
    fn init() {
        super::init_with_paths(vec![]).expect("failed to init config");
    }

    #[tokio::test]
    async fn watcher() {
        let temp_dir = tempdir().expect("failed to create temp dir");

        let secret_key_path = temp_dir.path().join("secret_key");
        let mut secret_key_file = File::create(&secret_key_path).expect("failed to create file");
        write!(secret_key_file, "my_secret_key").expect("failed to write to file");
        drop(secret_key_file);

        let config_file_path = temp_dir.path().join("config");
        let mut config_file = File::create(&config_file_path).expect("failed to create file");
        writeln!(
            config_file,
            "secret_key: file://{}\npostgresql:\n  password: my_postgres_pass",
            secret_key_path.display()
        )
        .expect("failed to write to file");
        drop(config_file);

        super::init_with_paths(vec![config_file_path.clone()]).expect("failed to init config");

        let mut tasks = Tasks::new().expect("failed to create tasks");
        let arbiter = tasks.arbiter();
        let mut events_rx = arbiter.events_subscribe();

        super::start(&mut tasks).expect("failed to start watcher");

        assert_eq!(super::get().secret_key, "my_secret_key");
        assert_eq!(super::get().postgresql.password, "my_postgres_pass");

        let _ = events_rx.recv().await;
        let mut secret_key_file = File::create(&secret_key_path).expect("failed to open file");
        write!(secret_key_file, "my_other_secret_key").expect("failed to write to file");
        drop(secret_key_file);

        assert_eq!(
            events_rx.recv().await.expect("failed to receive event"),
            Event::ConfigChanged,
        );
        while !events_rx.is_empty() {
            assert_eq!(
                events_rx.recv().await.expect("failed to receive event"),
                Event::ConfigChanged,
            );
        }

        assert_eq!(super::get().secret_key, "my_other_secret_key");
        assert_eq!(super::get().postgresql.password, "my_postgres_pass");

        let mut config_file = File::create(&config_file_path).expect("failed to open file");
        writeln!(
            config_file,
            "secret_key: file://{}\npostgresql:\n  password: my_new_postgres_pass",
            secret_key_path.display()
        )
        .expect("failed to write to file");
        drop(config_file);

        assert_eq!(
            events_rx.recv().await.expect("failed to receive event"),
            Event::ConfigChanged,
        );
        while !events_rx.is_empty() {
            assert_eq!(
                events_rx.recv().await.expect("failed to receive event"),
                Event::ConfigChanged,
            );
        }

        assert_eq!(super::get().secret_key, "my_other_secret_key");
        assert_eq!(super::get().postgresql.password, "my_new_postgres_pass");
    }

    /// Replace the files in `dir` the way the kubelet updates a mounted `Secret` or `ConfigMap`:
    /// write a new timestamped directory, atomically repoint `..data` at it, then delete the
    /// previous one. Like the kubelet, only the first component of each key is linked into
    /// `..data`, so a nested key is reached through a symlinked directory.
    fn kubelet_atomic_write(dir: &Path, generation: u32, files: &[(&str, &str)]) {
        kubelet_swap(dir, generation, files);
        if generation > 0 {
            fs::remove_dir_all(dir.join(format!("..{}", generation - 1)))
                .expect("failed to remove previous timestamped dir");
        }
    }

    /// Like [`kubelet_atomic_write`], but pause between deleting the previous files and deleting
    /// the directories that held them, as a slow kubelet would.
    async fn kubelet_atomic_write_slow_cleanup(
        dir: &Path,
        generation: u32,
        files: &[(&str, &str)],
    ) {
        kubelet_swap(dir, generation, files);
        if generation > 0 {
            let previous = dir.join(format!("..{}", generation - 1));
            for (name, _) in files {
                fs::remove_file(previous.join(name)).expect("failed to remove previous file");
            }
            sleep(Duration::from_millis(500)).await;
            fs::remove_dir_all(previous).expect("failed to remove previous timestamped dir");
        }
    }

    /// Write a new timestamped directory and repoint `..data` at it.
    fn kubelet_swap(dir: &Path, generation: u32, files: &[(&str, &str)]) {
        let ts_dir = format!("..{generation}");
        for (name, content) in files {
            let file = dir.join(&ts_dir).join(name);
            fs::create_dir_all(file.parent().expect("file has a parent"))
                .expect("failed to create timestamped dir");
            fs::write(file, content).expect("failed to write file");
        }
        symlink(&ts_dir, dir.join("..data_tmp")).expect("failed to create ..data_tmp");
        fs::rename(dir.join("..data_tmp"), dir.join("..data")).expect("failed to swap ..data");
        for (name, _) in files {
            let first = Path::new(name).iter().next().expect("key is not empty");
            let link = dir.join(first);
            if link.symlink_metadata().is_err() {
                symlink(Path::new("..data").join(first), link).expect("failed to create symlink");
            }
        }
    }

    /// Load `config` and start the watcher, returning once it is running.
    async fn start_watcher(dir: &Path, config: &str) -> (Tasks, broadcast::Receiver<Event>) {
        let config_file_path = dir.join("config");
        fs::write(&config_file_path, config).expect("failed to write config file");
        super::init_with_paths(vec![config_file_path]).expect("failed to init config");

        let mut tasks = Tasks::new().expect("failed to create tasks");
        let mut events_rx = tasks.arbiter().events_subscribe();
        super::start(&mut tasks).expect("failed to start watcher");
        let _ = timeout(Duration::from_secs(10), events_rx.recv())
            .await
            .expect("watcher did not start");
        (tasks, events_rx)
    }

    /// Wait until `check` passes, consuming config change events in between.
    async fn wait_for_config(
        events_rx: &mut broadcast::Receiver<Event>,
        check: impl Fn() -> bool + Send + Sync,
    ) -> bool {
        timeout(Duration::from_secs(10), async {
            while !check() {
                if events_rx.recv().await.is_err() {
                    return false;
                }
            }
            true
        })
        .await
        .unwrap_or(false)
    }

    /// Every kubelet update of `key` must be picked up, not only the first one.
    async fn assert_kubelet_updates_reloaded(key: &str, slow_cleanup: bool) {
        let temp_dir = tempdir().expect("failed to create temp dir");
        let secret_dir = temp_dir.path().join("secret");
        fs::create_dir_all(&secret_dir).expect("failed to create secret dir");
        kubelet_atomic_write(&secret_dir, 0, &[(key, "first")]);
        let config = format!(
            "postgresql:\n  password: file://{}\n",
            secret_dir.join(key).display()
        );
        let (_tasks, mut events_rx) = start_watcher(temp_dir.path(), &config).await;
        assert_eq!(super::get().postgresql.password, "first");

        for (generation, password) in [(1, "second"), (2, "third"), (3, "fourth")] {
            if slow_cleanup {
                kubelet_atomic_write_slow_cleanup(&secret_dir, generation, &[(key, password)])
                    .await;
            } else {
                kubelet_atomic_write(&secret_dir, generation, &[(key, password)]);
            }
            let reloaded = wait_for_config(&mut events_rx, || {
                super::get().postgresql.password == password
            })
            .await;
            assert!(
                reloaded,
                "password not reloaded after update {generation}, still '{}'",
                super::get().postgresql.password,
            );
        }
    }

    #[tokio::test]
    async fn watcher_kubelet_atomic_write() {
        assert_kubelet_updates_reloaded("password", false).await;
    }

    #[tokio::test]
    async fn watcher_kubelet_atomic_write_nested_key() {
        assert_kubelet_updates_reloaded("sub/password", false).await;
    }

    #[tokio::test]
    async fn watcher_kubelet_atomic_write_nested_key_slow_cleanup() {
        assert_kubelet_updates_reloaded("sub/password", true).await;
    }

    #[tokio::test]
    async fn watcher_atomic_rename() {
        let temp_dir = tempdir().expect("failed to create temp dir");
        let secret_key_path = temp_dir.path().join("secret_key");
        fs::write(&secret_key_path, "first").expect("failed to write file");
        let config = format!("secret_key: file://{}\n", secret_key_path.display());
        let (_tasks, mut events_rx) = start_watcher(temp_dir.path(), &config).await;
        assert_eq!(super::get().secret_key, "first");

        // Save the way editors do: write a temporary file, then rename it over the original.
        for secret_key in ["second", "third"] {
            let tmp_path = temp_dir.path().join("secret_key.tmp");
            fs::write(&tmp_path, secret_key).expect("failed to write file");
            fs::rename(&tmp_path, &secret_key_path).expect("failed to rename file");
            assert!(
                wait_for_config(&mut events_rx, || super::get().secret_key == secret_key).await,
                "secret_key not reloaded, still '{}'",
                super::get().secret_key,
            );
        }
    }

    #[tokio::test]
    async fn watcher_unreadable_dir() {
        let temp_dir = tempdir().expect("failed to create temp dir");
        let private_dir = temp_dir.path().join("private");
        fs::create_dir_all(&private_dir).expect("failed to create dir");
        let secret_key_path = private_dir.join("secret_key");
        fs::write(&secret_key_path, "first").expect("failed to write file");
        // Traversable but not listable, like /etc/ssl/private: the directory cannot be watched.
        fs::set_permissions(&private_dir, Permissions::from_mode(0o300))
            .expect("failed to set permissions");

        let config = format!("secret_key: file://{}\n", secret_key_path.display());
        let (_tasks, mut events_rx) = start_watcher(temp_dir.path(), &config).await;
        assert_eq!(super::get().secret_key, "first");

        // Written in place, then replaced twice: only the file itself can be watched here.
        fs::write(&secret_key_path, "second").expect("failed to write file");
        let mut reloaded =
            wait_for_config(&mut events_rx, || super::get().secret_key == "second").await;
        for secret_key in ["third", "fourth"] {
            if !reloaded {
                break;
            }
            let tmp_path = private_dir.join("secret_key.tmp");
            fs::write(&tmp_path, secret_key).expect("failed to write file");
            fs::rename(&tmp_path, &secret_key_path).expect("failed to rename file");
            reloaded =
                wait_for_config(&mut events_rx, || super::get().secret_key == secret_key).await;
        }
        fs::set_permissions(&private_dir, Permissions::from_mode(0o700))
            .expect("failed to set permissions");
        assert!(
            reloaded,
            "secret_key not reloaded, still '{}'",
            super::get().secret_key
        );
    }

    #[tokio::test]
    async fn watcher_file_temporarily_unreadable() {
        let temp_dir = tempdir().expect("failed to create temp dir");
        let private_dir = temp_dir.path().join("private");
        fs::create_dir_all(&private_dir).expect("failed to create dir");
        let secret_key_path = private_dir.join("secret_key");
        fs::write(&secret_key_path, "first").expect("failed to write file");
        fs::set_permissions(&private_dir, Permissions::from_mode(0o300))
            .expect("failed to set permissions");

        let config = format!("secret_key: file://{}\n", secret_key_path.display());
        let (_tasks, mut events_rx) = start_watcher(temp_dir.path(), &config).await;
        assert_eq!(super::get().secret_key, "first");

        // While the file is unreadable, a new watcher can watch neither it nor its directory.
        fs::set_permissions(&secret_key_path, Permissions::from_mode(0o000))
            .expect("failed to set permissions");
        let noticed = timeout(Duration::from_secs(10), events_rx.recv())
            .await
            .is_ok();
        fs::set_permissions(&secret_key_path, Permissions::from_mode(0o600))
            .expect("failed to set permissions");
        fs::write(&secret_key_path, "second").expect("failed to write file");
        let reloaded = noticed
            && wait_for_config(&mut events_rx, || super::get().secret_key == "second").await;
        fs::set_permissions(&private_dir, Permissions::from_mode(0o700))
            .expect("failed to set permissions");
        assert!(
            reloaded,
            "secret_key not reloaded, still '{}'",
            super::get().secret_key
        );
    }

    /// Renaming a file away applies its fallback, and renaming it back and writing to it is
    /// picked up, in a directory with `mode`.
    async fn assert_renamed_away_and_back_reloaded(mode: u32) {
        let temp_dir = tempdir().expect("failed to create temp dir");
        let private_dir = temp_dir.path().join("private");
        fs::create_dir_all(&private_dir).expect("failed to create dir");
        let secret_key_path = private_dir.join("secret_key");
        let backup_path = private_dir.join("secret_key.bak");
        fs::write(&secret_key_path, "first").expect("failed to write file");
        fs::set_permissions(&private_dir, Permissions::from_mode(mode))
            .expect("failed to set permissions");

        let config = format!(
            "secret_key: file://{}?fallback\n",
            secret_key_path.display()
        );
        let (_tasks, mut events_rx) = start_watcher(temp_dir.path(), &config).await;
        assert_eq!(super::get().secret_key, "first");

        fs::rename(&secret_key_path, &backup_path).expect("failed to rename file");
        let mut reloaded =
            wait_for_config(&mut events_rx, || super::get().secret_key == "fallback").await;
        if reloaded {
            fs::rename(&backup_path, &secret_key_path).expect("failed to rename file");
            reloaded = wait_for_config(&mut events_rx, || super::get().secret_key == "first").await;
        }
        if reloaded {
            fs::write(&secret_key_path, "second").expect("failed to write file");
            reloaded =
                wait_for_config(&mut events_rx, || super::get().secret_key == "second").await;
        }
        fs::set_permissions(&private_dir, Permissions::from_mode(0o700))
            .expect("failed to set permissions");
        assert!(
            reloaded,
            "secret_key not reloaded, still '{}'",
            super::get().secret_key
        );
    }

    #[tokio::test]
    async fn watcher_file_renamed_away_and_back() {
        assert_renamed_away_and_back_reloaded(0o700).await;
    }

    #[tokio::test]
    async fn watcher_file_renamed_away_and_back_in_unreadable_dir() {
        // Only the watch of the file itself can notice it coming back.
        assert_renamed_away_and_back_reloaded(0o300).await;
    }

    #[tokio::test]
    async fn watcher_file_removed_uses_fallback() {
        let temp_dir = tempdir().expect("failed to create temp dir");
        let secret_key_path = temp_dir.path().join("secret_key");
        fs::write(&secret_key_path, "first").expect("failed to write file");
        let config = format!(
            "secret_key: file://{}?fallback\n",
            secret_key_path.display()
        );
        let (_tasks, mut events_rx) = start_watcher(temp_dir.path(), &config).await;
        assert_eq!(super::get().secret_key, "first");

        fs::remove_file(&secret_key_path).expect("failed to remove file");
        assert!(
            wait_for_config(&mut events_rx, || super::get().secret_key == "fallback").await,
            "fallback not used, still '{}'",
            super::get().secret_key,
        );

        fs::write(&secret_key_path, "second").expect("failed to write file");
        assert!(
            wait_for_config(&mut events_rx, || super::get().secret_key == "second").await,
            "secret_key not reloaded, still '{}'",
            super::get().secret_key,
        );
    }

    /// Number of inotify watches held by this process.
    #[cfg(target_os = "linux")]
    fn inotify_watch_count() -> usize {
        fs::read_dir("/proc/self/fd")
            .expect("failed to list file descriptors")
            .filter_map(Result::ok)
            .filter(|fd| {
                fs::read_link(fd.path())
                    .is_ok_and(|target| target == Path::new("anon_inode:inotify"))
            })
            .filter_map(|fd| {
                fs::read_to_string(Path::new("/proc/self/fdinfo").join(fd.file_name())).ok()
            })
            .map(|info| {
                info.lines()
                    .filter(|line| line.starts_with("inotify wd:"))
                    .count()
            })
            .sum()
    }

    #[cfg(target_os = "linux")]
    #[tokio::test]
    async fn watcher_does_not_leak_watches() {
        let temp_dir = tempdir().expect("failed to create temp dir");
        let releases = temp_dir.path().join("releases");
        fs::create_dir_all(&releases).expect("failed to create dir");
        fs::write(releases.join("0"), "0").expect("failed to write file");
        let link = temp_dir.path().join("password");
        symlink(releases.join("0"), &link).expect("failed to create symlink");

        let config = format!("postgresql:\n  password: file://{}\n", link.display());
        let (_tasks, mut events_rx) = start_watcher(temp_dir.path(), &config).await;
        let watches_at_start = inotify_watch_count();

        // Repoint the symlink while keeping every previous target, so no watch dies on its own.
        for release in 1_u32..=10 {
            let target = releases.join(release.to_string());
            fs::write(&target, release.to_string()).expect("failed to write file");
            let tmp_link = temp_dir.path().join("password.tmp");
            symlink(&target, &tmp_link).expect("failed to create symlink");
            fs::rename(&tmp_link, &link).expect("failed to swap symlink");
            let expected = release.to_string();
            assert!(
                wait_for_config(&mut events_rx, || super::get().postgresql.password
                    == expected)
                .await,
                "password not reloaded after release {release}",
            );
        }

        // A replaced watcher releases its watches shortly after it is dropped.
        let settled = timeout(Duration::from_secs(5), async {
            while inotify_watch_count() > watches_at_start {
                sleep(Duration::from_millis(50)).await;
            }
        })
        .await
        .is_ok();
        assert!(
            settled,
            "inotify watches grew from {watches_at_start} to {}",
            inotify_watch_count()
        );
    }

    #[tokio::test]
    async fn watcher_symlink_into_kubelet_volume() {
        let temp_dir = tempdir().expect("failed to create temp dir");
        let volume = temp_dir.path().join("volume");
        fs::create_dir_all(&volume).expect("failed to create dir");
        kubelet_atomic_write(&volume, 0, &[("password", "first")]);
        let link_dir = temp_dir.path().join("links");
        fs::create_dir_all(&link_dir).expect("failed to create dir");
        let link = link_dir.join("password");
        symlink(volume.join("password"), &link).expect("failed to create symlink");

        let config = format!("postgresql:\n  password: file://{}\n", link.display());
        let (_tasks, mut events_rx) = start_watcher(temp_dir.path(), &config).await;
        assert_eq!(super::get().postgresql.password, "first");

        for (generation, password) in [(1, "second"), (2, "third"), (3, "fourth")] {
            kubelet_atomic_write(&volume, generation, &[("password", password)]);
            let reloaded = wait_for_config(&mut events_rx, || {
                super::get().postgresql.password == password
            })
            .await;
            assert!(
                reloaded,
                "password not reloaded after update {generation}, still '{}'",
                super::get().postgresql.password,
            );
        }
    }

    #[tokio::test]
    async fn watcher_file_created_later() {
        let temp_dir = tempdir().expect("failed to create temp dir");
        let secret_key_path = temp_dir.path().join("secret_key");
        let config = format!("secret_key: file://{}\n", secret_key_path.display());
        let (_tasks, mut events_rx) = start_watcher(temp_dir.path(), &config).await;
        assert_eq!(super::get().secret_key, "");

        fs::write(&secret_key_path, "created").expect("failed to write file");
        assert!(
            wait_for_config(&mut events_rx, || super::get().secret_key == "created").await,
            "secret_key not reloaded, still '{}'",
            super::get().secret_key,
        );
    }

    fn event(kind: EventKind, paths: &[&Path]) -> notify::Event {
        paths.iter().fold(notify::Event::new(kind), |ev, path| {
            ev.add_path(path.to_path_buf())
        })
    }

    #[test]
    fn change_detector_ignores_reads_and_other_files() {
        let temp_dir = tempdir().expect("failed to create temp dir");
        let watched = temp_dir.path().join("watched");
        let other = temp_dir.path().join("other");
        fs::write(&watched, "value").expect("failed to write file");
        fs::write(&other, "value").expect("failed to write file");
        let mut detector = super::ChangeDetector::new(std::slice::from_ref(&watched));

        assert!(!detector.is_change(&event(EventKind::Access(AccessKind::Any), &[&watched])));
        assert!(!detector.is_change(&event(
            EventKind::Modify(ModifyKind::Data(DataChange::Any)),
            &[&other]
        )));
    }

    #[test]
    fn change_detector_file_written_or_created() {
        let temp_dir = tempdir().expect("failed to create temp dir");
        let watched = temp_dir.path().join("watched");
        fs::write(&watched, "value").expect("failed to write file");
        let mut detector = super::ChangeDetector::new(std::slice::from_ref(&watched));

        assert!(detector.is_change(&event(
            EventKind::Modify(ModifyKind::Data(DataChange::Any)),
            &[&watched]
        )));
        assert!(detector.is_change(&event(EventKind::Create(CreateKind::File), &[&watched])));
    }

    #[test]
    fn change_detector_renamed_away_and_back() {
        let temp_dir = tempdir().expect("failed to create temp dir");
        let watched = temp_dir.path().join("watched");
        let backup = temp_dir.path().join("watched.bak");
        fs::write(&watched, "value").expect("failed to write file");
        let mut detector = super::ChangeDetector::new(std::slice::from_ref(&watched));
        let rename = EventKind::Modify(ModifyKind::Name(RenameMode::Both));

        fs::rename(&watched, &backup).expect("failed to rename file");
        assert!(detector.is_change(&event(rename, &[&watched, &backup])));
        assert!(!detector.is_change(&event(EventKind::Remove(RemoveKind::File), &[&watched])));

        fs::rename(&backup, &watched).expect("failed to rename file");
        assert!(detector.is_change(&event(rename, &[&backup, &watched])));
    }

    #[test]
    fn change_detector_symlink_target_changed() {
        let temp_dir = tempdir().expect("failed to create temp dir");
        fs::write(temp_dir.path().join("first"), "first").expect("failed to write file");
        fs::write(temp_dir.path().join("second"), "second").expect("failed to write file");
        let watched = temp_dir.path().join("watched");
        symlink("first", &watched).expect("failed to create symlink");
        let mut detector = super::ChangeDetector::new(std::slice::from_ref(&watched));

        let tmp_link = temp_dir.path().join("watched.tmp");
        symlink("second", &tmp_link).expect("failed to create symlink");
        fs::rename(&tmp_link, &watched).expect("failed to swap symlink");

        // The event names another entry of the directory, but the file now resolves elsewhere.
        let unrelated = event(EventKind::Create(CreateKind::Any), &[&tmp_link]);
        assert!(detector.is_change(&unrelated));
        assert!(!detector.is_change(&unrelated));
    }

    #[test]
    fn change_detector_file_removed_then_recreated() {
        let temp_dir = tempdir().expect("failed to create temp dir");
        let watched = temp_dir.path().join("watched");
        fs::write(&watched, "value").expect("failed to write file");
        let mut detector = super::ChangeDetector::new(std::slice::from_ref(&watched));

        fs::remove_file(&watched).expect("failed to remove file");
        let metadata_changed = EventKind::Modify(ModifyKind::Metadata(MetadataKind::Any));
        assert!(detector.is_change(&event(metadata_changed, &[&watched])));
        assert!(!detector.is_change(&event(EventKind::Remove(RemoveKind::File), &[&watched])));

        fs::write(&watched, "value").expect("failed to write file");
        assert!(detector.is_change(&event(EventKind::Create(CreateKind::File), &[&watched])));
    }

    #[test]
    fn change_detector_events_dropped() {
        let temp_dir = tempdir().expect("failed to create temp dir");
        let watched = temp_dir.path().join("watched");
        fs::write(&watched, "value").expect("failed to write file");
        let mut detector = super::ChangeDetector::new(std::slice::from_ref(&watched));

        assert!(detector.is_change(&notify::Event::new(EventKind::Other).set_flag(Flag::Rescan)));
    }

    #[test]
    fn change_detector_event_about_symlink_target() {
        let temp_dir = tempdir().expect("failed to create temp dir");
        let secrets = temp_dir.path().join("secrets");
        let links = temp_dir.path().join("links");
        fs::create_dir_all(&secrets).expect("failed to create dir");
        fs::create_dir_all(&links).expect("failed to create dir");
        fs::write(secrets.join("password"), "value").expect("failed to write file");
        let watched = links.join("password");
        symlink(secrets.join("password"), &watched).expect("failed to create symlink");
        let mut detector = super::ChangeDetector::new(std::slice::from_ref(&watched));

        // Some platforms, macOS included, report events by the real path of the file.
        assert!(detector.is_change(&event(
            EventKind::Modify(ModifyKind::Data(DataChange::Any)),
            &[&fs::canonicalize(secrets.join("password")).expect("failed to resolve path")]
        )));
    }

    #[test]
    fn change_detector_event_through_real_dir() {
        let temp_dir = tempdir().expect("failed to create temp dir");
        let real_dir = temp_dir.path().join("real");
        fs::create_dir_all(&real_dir).expect("failed to create dir");
        symlink(&real_dir, temp_dir.path().join("alias")).expect("failed to create symlink");
        let watched = temp_dir.path().join("alias").join("watched");
        fs::write(&watched, "value").expect("failed to write file");
        let mut detector = super::ChangeDetector::new(std::slice::from_ref(&watched));

        // Some platforms, macOS included, report events by the directory's real path.
        assert!(
            detector.is_change(&event(
                EventKind::Modify(ModifyKind::Data(DataChange::Any)),
                &[&fs::canonicalize(&real_dir)
                    .expect("failed to resolve path")
                    .join("watched")]
            ))
        );
    }

    /// A watcher that records what it watches, or fails with `failure` to watch `failing_path`,
    /// or every path if that is not set.
    #[derive(Default)]
    struct FakeWatcher {
        id: u8,
        watched: Vec<PathBuf>,
        failure: Option<fn() -> notify::ErrorKind>,
        failing_path: Option<PathBuf>,
    }

    #[expect(clippy::missing_trait_methods, reason = "test double")]
    impl notify::Watcher for FakeWatcher {
        fn new<F: notify::EventHandler>(_: F, _: notify::Config) -> notify::Result<Self> {
            Ok(Self::default())
        }

        fn watch(&mut self, path: &Path, _: notify::RecursiveMode) -> notify::Result<()> {
            if let Some(failure) = self.failure
                && self.failing_path.as_deref().is_none_or(|p| p == path)
            {
                return Err(notify::Error::new(failure()));
            }
            self.watched.push(path.to_path_buf());
            Ok(())
        }

        fn unwatch(&mut self, _: &Path) -> notify::Result<()> {
            Ok(())
        }

        fn kind() -> notify::WatcherKind {
            notify::WatcherKind::NullWatcher
        }
    }

    /// Hand over from a watcher in `state` for a single path, returning the resulting watcher
    /// and state.
    fn handed_over(
        state: WatchState,
        replacement: notify::Result<FakeWatcher>,
    ) -> (FakeWatcher, WatchState) {
        let mut current = FakeWatcher {
            id: 1,
            ..FakeWatcher::default()
        };
        let mut states = [state];
        super::hand_over(
            &mut current,
            &mut states,
            replacement,
            &[PathBuf::from("/config")],
        );
        (current, states[0])
    }

    fn failing_watcher(failure: fn() -> notify::ErrorKind) -> FakeWatcher {
        FakeWatcher {
            id: 2,
            failure: Some(failure),
            ..FakeWatcher::default()
        }
    }

    fn permission_denied() -> notify::ErrorKind {
        notify::ErrorKind::Io(io::Error::from(io::ErrorKind::PermissionDenied))
    }

    #[test]
    fn hand_over_replaces_current_watcher() {
        let replacement = Ok(FakeWatcher {
            id: 2,
            ..FakeWatcher::default()
        });
        let (current, state) = handed_over(WatchState::Watched, replacement);
        assert_eq!(current.id, 2);
        assert_eq!(current.watched, [PathBuf::from("/config")]);
        assert_eq!(state, WatchState::Watched);
    }

    #[test]
    fn hand_over_ignores_missing_files_in_watched_dirs() {
        // The directory watch notices the file coming back.
        let file = PathBuf::from("/secrets/password");
        let replacement = FakeWatcher {
            failing_path: Some(file.clone()),
            ..failing_watcher(|| notify::ErrorKind::PathNotFound)
        };
        let mut current = FakeWatcher {
            id: 1,
            ..FakeWatcher::default()
        };
        let mut states = [WatchState::Watched, WatchState::Watched];
        super::hand_over(
            &mut current,
            &mut states,
            Ok(replacement),
            &[file, PathBuf::from("/secrets")],
        );
        assert_eq!(current.id, 2);
        assert_eq!(states, [WatchState::Missing, WatchState::Watched]);
    }

    #[test]
    fn hand_over_keeps_current_watcher_when_a_missing_file_has_no_watched_dir() {
        // Only the current watch notices a file that was renamed away coming back.
        let replacement = Ok(failing_watcher(|| notify::ErrorKind::PathNotFound));
        let (current, state) = handed_over(WatchState::Watched, replacement);
        assert_eq!(current.id, 1);
        assert_eq!(state, WatchState::Watched);
    }

    #[test]
    fn hand_over_ignores_paths_the_current_watcher_does_not_watch() {
        // An unreadable directory the current watcher could not watch either.
        let (current, state) =
            handed_over(WatchState::Failed, Ok(failing_watcher(permission_denied)));
        assert_eq!(current.id, 2);
        assert_eq!(state, WatchState::Failed);
    }

    #[test]
    fn hand_over_keeps_current_watcher_when_a_watch_would_be_lost() {
        // A file that is no longer readable.
        let (current, state) =
            handed_over(WatchState::Watched, Ok(failing_watcher(permission_denied)));
        assert_eq!(current.id, 1);
        assert_eq!(state, WatchState::Watched);
    }

    #[test]
    fn hand_over_keeps_current_watcher_when_out_of_watches() {
        let replacement = Ok(failing_watcher(|| notify::ErrorKind::MaxFilesWatch));
        let (current, state) = handed_over(WatchState::Watched, replacement);
        assert_eq!(current.id, 1);
        assert_eq!(state, WatchState::Watched);
    }

    #[test]
    fn hand_over_keeps_current_watcher_when_creation_fails() {
        let replacement = Err(notify::Error::generic("no inotify instance left"));
        let (current, state) = handed_over(WatchState::Watched, replacement);
        assert_eq!(current.id, 1);
        assert_eq!(state, WatchState::Watched);
    }

    #[test]
    fn set() {
        super::init_with_paths(vec![]).expect("failed to init config");
        assert_eq!(super::get().secret_key, String::new());
        super::set(json!({"secret_key": "my_new_secret_key"})).expect("failed to set config");
        assert_eq!(super::get().secret_key, "my_new_secret_key");
    }

    #[test]
    fn env_bool_true() {
        #[expect(unsafe_code, reason = "testing")]
        // SAFETY: testing
        unsafe {
            env::set_var("AUTHENTIK_DEBUG", "true");
        }

        let (config, _) = super::Config::load(&[], None).expect("failed to load config");

        assert!(config.debug);
    }

    #[test]
    fn env_bool_false() {
        #[expect(unsafe_code, reason = "testing")]
        // SAFETY: testing
        unsafe {
            env::set_var("AUTHENTIK_DEBUG", "false");
        }

        let (config, _) = super::Config::load(&[], None).expect("failed to load config");

        assert!(!config.debug);
    }

    #[test]
    fn env_list_empty() {
        #[expect(unsafe_code, reason = "testing")]
        // SAFETY: testing
        unsafe {
            env::set_var("AUTHENTIK_LISTEN__HTTP", "");
        }

        let (config, _) = super::Config::load(&[], None).expect("failed to load config");

        assert_eq!(config.listen.http, []);
    }

    #[test]
    fn env_list_one_element() {
        #[expect(unsafe_code, reason = "testing")]
        // SAFETY: testing
        unsafe {
            env::set_var("AUTHENTIK_LISTEN__HTTP", "[::1]:9000");
        }

        let (config, _) = super::Config::load(&[], None).expect("failed to load config");

        assert_eq!(
            config.listen.http,
            ["[::1]:9000".parse().expect("infallible")]
        );
    }

    #[test]
    fn env_list_many_elements() {
        #[expect(unsafe_code, reason = "testing")]
        // SAFETY: testing
        unsafe {
            env::set_var("AUTHENTIK_LISTEN__HTTP", "[::1]:9000,[::1]:9001");
        }

        let (config, _) = super::Config::load(&[], None).expect("failed to load config");

        assert_eq!(
            config.listen.http,
            [
                "[::1]:9000".parse().expect("infallible"),
                "[::1]:9001".parse().expect("infallible")
            ]
        );
    }

    #[test]
    fn env_string() {
        #[expect(unsafe_code, reason = "testing")]
        // SAFETY: testing
        unsafe {
            env::set_var("AUTHENTIK_SECRET_KEY", "my_secret_key");
        }

        let (config, _) = super::Config::load(&[], None).expect("failed to load config");

        assert_eq!(config.secret_key, "my_secret_key",);
    }
}
