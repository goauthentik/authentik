use std::{
    env,
    fs::{self, read_to_string},
    path::PathBuf,
    sync::{Arc, OnceLock},
};

use arc_swap::{ArcSwap, Guard};
use eyre::Result;
use notify::{RecommendedWatcher, Watcher};
use serde_json::{Map, Value};
use tokio::sync::mpsc;
use tracing::{error, info, warn};

pub(crate) mod schema;

pub(crate) use schema::Config;
use url::Url;

use crate::arbiter::{Arbiter, Tasks};

static DEFAULT_CONFIG: &str = include_str!("../../authentik/lib/default.yml");
static CONFIG_MANAGER: OnceLock<ConfigManager> = OnceLock::new();

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
    fn load_raw(config_paths: &[PathBuf]) -> Result<Value> {
        let mut builder = config::Config::builder().add_source(config::File::from_str(
            DEFAULT_CONFIG,
            config::FileFormat::Yaml,
        ));
        for path in config_paths {
            builder = builder
                .add_source(config::File::from(path.as_path()).format(config::FileFormat::Yaml));
        }
        builder = builder.add_source(config::Environment::with_prefix("AUTHENTIK"));
        let config = builder.build()?;
        let raw = config.try_deserialize::<Value>()?;
        Ok(raw)
    }

    fn expand_value(value: &str) -> (String, Option<PathBuf>) {
        let value = value.trim();
        if let Ok(uri) = Url::parse(value) {
            let fallback = uri.query().unwrap_or("").to_owned();
            match uri.scheme() {
                "file" => {
                    let path = uri.path();
                    match read_to_string(path).map(|s| s.trim().to_owned()) {
                        Ok(value) => return (value.to_owned(), Some(PathBuf::from(path))),
                        Err(err) => {
                            error!("failed to read config value from {path}: {err}");
                            return (fallback, Some(PathBuf::from(path)));
                        }
                    }
                }
                "env" => {
                    if let Some(var) = uri.host_str() {
                        if let Ok(value) = env::var(var) {
                            return (value.to_owned(), None);
                        } else {
                            return (fallback, None);
                        }
                    }
                }
                _ => {}
            };
        }

        (value.to_owned(), None)
    }

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

    fn load(config_paths: &[PathBuf]) -> Result<(Config, Vec<PathBuf>)> {
        let raw = Self::load_raw(config_paths)?;
        let (expanded, file_paths) = Self::expand(raw);
        let config: Config = serde_json::from_value(expanded)?;
        Ok((config, file_paths))
    }
}

pub(crate) struct ConfigManager {
    config: ArcSwap<Config>,
    config_paths: Vec<PathBuf>,
    watch_paths: Vec<PathBuf>,
}

impl ConfigManager {
    pub(crate) fn init() -> Result<()> {
        info!("loading config");
        let config_paths = config_paths();
        let mut watch_paths = config_paths.clone();
        let (config, other_paths) = Config::load(&config_paths)?;
        watch_paths.extend(other_paths);
        let manager = Self {
            config: ArcSwap::from_pointee(config),
            config_paths,
            watch_paths,
        };
        CONFIG_MANAGER.get_or_init(|| manager);
        info!("config loaded");
        Ok(())
    }

    pub(crate) fn run(tasks: &mut Tasks) -> Result<()> {
        info!("starting config file watcher");
        let arbiter = tasks.arbiter();
        tasks
            .build_task()
            .name(&format!("{}::watch_config", module_path!()))
            .spawn(watch_config(arbiter))?;
        Ok(())
    }
}

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

    info!("config file watcher started on paths: {:?}", watch_paths);

    loop {
        tokio::select! {
            res = rx.recv() => {
                info!("a configuration file changed, reloading config");
                if res.is_none() {
                    break;
                }
                let manager = CONFIG_MANAGER.get().expect("failed to get config, has it been initialized?");
                match tokio::task::spawn_blocking(|| Config::load(&manager.config_paths)).await? {
                    Ok((new_config, _)) => {
                        info!("configuration reloaded");
                        manager.config.store(Arc::new(new_config));
                        if let Err(err) = arbiter.config_changed_send(()) {
                            warn!("failed to notify of config change, aborting: {err:?}");
                            break;
                        }
                    }
                    Err(err) => {
                        warn!("failed to reload config, continuing with previous config: {err:?}");
                    }
                }
            },
            () = arbiter.shutdown() => break,
        }
    }

    info!("stopping config file watcher");

    Ok(())
}

pub(crate) fn get() -> Guard<Arc<Config>> {
    let manager = CONFIG_MANAGER
        .get()
        .expect("failed to get config, has it been initialized?");
    manager.config.load()
}
