use std::{env, fs, path::PathBuf, sync::OnceLock};

use eyre::Result;
use notify::{RecommendedWatcher, Watcher};
use serde_json::{Map, Value};
use tokio::{
    fs::read_to_string,
    sync::{RwLock, RwLockReadGuard, broadcast, mpsc},
    task::JoinSet,
};
use tokio_util::sync::CancellationToken;
use tracing::trace;

pub mod schema;
mod source;

pub use crate::schema::Config;
use crate::source::AsyncFile;

static DEFAULT_CONFIG: &str = include_str!("../../../authentik/lib/default.yml");
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
                path.join(format!("{}.yml", environment)),
                path.join(format!("{}.env.yml", environment)),
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
    async fn load_raw(config_paths: &[PathBuf]) -> Result<Value> {
        let mut builder =
            config::ConfigBuilder::<config::builder::AsyncState>::default().add_source(
                config::File::from_str(DEFAULT_CONFIG, config::FileFormat::Yaml),
            );
        for path in config_paths {
            builder = builder.add_async_source(AsyncFile {
                name: path.clone(),
                format: config::FileFormat::Yaml,
            });
        }
        builder = builder.add_source(config::Environment::with_prefix("AUTHENTIK"));
        let config = builder.build().await?;
        let raw = config.try_deserialize::<Value>()?;
        Ok(raw)
    }

    // TODO: fallback values
    async fn expand_value(value: &str) -> Result<(String, Option<PathBuf>)> {
        let trimmed = value.trim();
        let value = if let Some(path) = trimmed.strip_prefix("file://") {
            (
                read_to_string(path).await.map(|s| s.trim().to_owned())?,
                Some(PathBuf::from(path)),
            )
        } else if let Some(env_var) = trimmed.strip_prefix("env://") {
            (env::var(env_var)?, None)
        } else {
            (value.to_owned(), None)
        };
        Ok(value)
    }

    async fn expand(mut raw: Value) -> (Value, Vec<PathBuf>) {
        let mut file_paths = Vec::new();
        let value = match &mut raw {
            Value::String(s) => {
                if let Ok(expanded) = Self::expand_value(s).await {
                    let (v, path) = expanded;
                    if let Some(path) = path {
                        file_paths.push(path);
                    }
                    Value::String(v)
                } else {
                    raw
                }
            }
            Value::Array(arr) => {
                let mut res = Vec::with_capacity(arr.len());
                for v in arr {
                    let (expanded, paths) = Box::pin(Self::expand(v.clone())).await;
                    file_paths.extend(paths);
                    res.push(expanded);
                }
                Value::Array(res)
            }
            Value::Object(map) => {
                let mut res = Map::with_capacity(map.len());
                for (k, v) in map {
                    let (expanded, paths) = Box::pin(Self::expand(v.clone())).await;
                    file_paths.extend(paths);
                    res.insert(k.clone(), expanded);
                }
                Value::Object(res)
            }
            _ => raw,
        };
        (value, file_paths)
    }

    async fn load(config_paths: &[PathBuf]) -> Result<(Config, Vec<PathBuf>)> {
        let raw = Self::load_raw(config_paths).await?;
        let (expanded, file_paths) = Self::expand(raw).await;
        let config: Config = serde_json::from_value(expanded)?;
        Ok((config, file_paths))
    }
}

pub struct ConfigManager {
    config: RwLock<Config>,
    config_paths: Vec<PathBuf>,
}

impl ConfigManager {
    pub async fn init(
        tasks: &mut JoinSet<Result<()>>,
        stop: CancellationToken,
        config_changed_tx: broadcast::Sender<()>,
    ) -> Result<()> {
        let config_paths = config_paths();
        let mut watch_paths = config_paths.clone();
        let (config, other_paths) = Config::load(&config_paths).await?;
        watch_paths.extend(other_paths);
        let manager = Self {
            config: RwLock::new(config),
            config_paths,
        };
        CONFIG_MANAGER.get_or_init(|| manager);
        tasks.spawn(watch_config(stop, watch_paths, config_changed_tx));
        Ok(())
    }
}

async fn watch_config(
    stop: CancellationToken,
    watch_paths: Vec<PathBuf>,
    config_changed_tx: broadcast::Sender<()>,
) -> Result<()> {
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
    for path in watch_paths {
        watcher.watch(path.as_ref(), notify::RecursiveMode::NonRecursive)?;
    }

    loop {
        tokio::select! {
            res = rx.recv() => {
                if res.is_none() {
                    break;
                }
                let manager = CONFIG_MANAGER.get().unwrap();
                if let Ok((new_config, _)) = Config::load(&manager.config_paths).await {
                    trace!("Configuration file changed, reloading");
                    let mut config = manager.config.write().await;
                    *config = new_config;
                    drop(config);
                    if config_changed_tx.send(()).is_err() {
                        break;
                    }
                };
            },
            _ = stop.cancelled() => break,
        }
    }

    Ok(())
}

pub async fn get_config<'a>() -> RwLockReadGuard<'a, Config> {
    let manager = CONFIG_MANAGER.get().unwrap();
    manager.config.read().await
}
