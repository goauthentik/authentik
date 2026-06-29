use std::{
    env,
    fs::{self, read_to_string},
    path::PathBuf,
    sync::{Arc, OnceLock},
};

use arc_swap::ArcSwap;
use eyre::Result;
use notify::{RecommendedWatcher, Watcher as _};
use serde_json::{Map, Value};
use tokio::{sync::mpsc, task::spawn_blocking};
use tracing::{error, info, warn};
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

/// Watch for configuration changes, reload the configuration in memory and send events.
///
/// [`init`] must be called before this is used.
async fn watch_config(arbiter: Arbiter) -> Result<()> {
    let (tx, mut rx) = mpsc::channel(100);
    let mut watcher = RecommendedWatcher::new(
        move |res: notify::Result<notify::Event>| {
            if let Ok(event) = res
                && let notify::EventKind::Modify(_) = &event.kind
            {
                let _ = tx.blocking_send(());
            }
        },
        notify::Config::default(),
    )?;
    let watch_paths = &CONFIG_MANAGER
        .get()
        .expect("failed to get config, has it been initialized?")
        .watch_paths;
    for path in watch_paths {
        watcher.watch(path.as_ref(), notify::RecursiveMode::NonRecursive)?;
    }

    let _ = arbiter.send_event(Event::ConfigChanged);
    info!(paths = ?watch_paths, "config file watcher started");

    loop {
        tokio::select! {
            res = rx.recv() => {
                info!("a configuration file changed, reloading config");
                if res.is_none() {
                    break;
                }
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
    use std::{env, fs::File, io::Write as _, path::PathBuf};

    use serde_json::json;
    use tempfile::tempdir;

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

    // See https://github.com/rust-cli/config-rs/issues/443
    // #[test]
    // fn env_list_empty() {
    //     #[expect(unsafe_code, reason = "testing")]
    //     // SAFETY: testing
    //     unsafe {
    //         env::set_var("AUTHENTIK_LISTEN__HTTP", "");
    //     }
    //
    //     let (config, _) = super::Config::load(&[], None).expect("failed to load config");
    //
    //     assert_eq!(config.listen.http, []);
    // }

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
