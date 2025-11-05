use std::{
    env, fs,
    path::{Path, PathBuf},
    sync::OnceLock,
};

use miette::Result;
use serde::{Deserialize, Serialize};

static DEFAULT_CONFIG: &str = include_str!("../../../authentik/lib/default.yml");
static CONFIG: OnceLock<Config> = OnceLock::new();

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    // Core specific config
    storage: StorageConfig,
    log_level: String,
    error_reporting: ErrorReportingConfig,
    postgresql: PostgreSQLConfig,
    outposts: OutpostConfig,

    // Config for core and embedded outpost
    secret_key: String,

    // Config for both core and ouposts
    debug: bool,
    listen: ListenConfig,
    web: WebConfig,

    // Outpost specific config
    // These are only relevant for outposts, and cannot be set via YAML
    // They are loaded via this config loader to support file:// schemas
    authentik_host: String,
    authentik_host_browser: String,
    authentik_token: String,
    authentik_insecure: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct StorageConfig {
    media: StorageMediaConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct StorageMediaConfig {
    backend: String,
    file: StorageFileConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct StorageFileConfig {
    path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct ErrorReportingConfig {
    enabled: bool,
    sentry_dsn: String,
    environment: String,
    send_pii: bool,
    sample_rate: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct PostgreSQLConfig {
    host: String,
    port: u32,
    user: String,
    password: String,
    name: String,

    // SSL/TLS settings
    sslmode: String,
    sslrootcert: String,
    sslcert: String,
    sslkey: String,

    // Connection management
    conn_max_age: u32,
    conn_health_checks: bool,
    disable_server_side_cursors: bool,

    // Advanced settings
    default_schema: String,
    conn_options: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct OutpostConfig {
    container_image_base: String,
    discover: bool,
    disable_embedded_outpost: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct ListenConfig {
    http: String,
    https: String,
    ldap: String,
    ldaps: String,
    radius: String,
    metrics: String,
    debug: String,
    trusted_proxy_cidrs: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct WebConfig {
    path: String,
}

impl Default for Config {
    fn default() -> Self {
        serde_yaml_ng::from_str(DEFAULT_CONFIG).expect("Failed to parse embedded default config")
    }
}

impl Config {
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
            let Ok(abs_path) = path.canonicalize().or_else(|_| fs::canonicalize(&path)) else {
                continue;
            };

            if let Ok(metadata) = fs::metadata(&abs_path) {
                if !metadata.is_dir() {
                    computed_paths.push(abs_path);
                } else {
                    let env_paths = vec![
                        abs_path.join(format!("{}.yml", environment)),
                        abs_path.join(format!("{}.env.yml", environment)),
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
        }

        computed_paths
    }

    fn load_raw() {
        let mut builder = config::Config::builder();
        for path in Self::config_paths() {
            builder = builder.add_source(config::File::from(path));
        }
        builder = builder.add_source(config::Environment::with_prefix("AUTHENTIK"));
    }

    pub fn setup() {
        let config = Self::default();
    }
}
