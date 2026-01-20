use std::{env, fs, net::SocketAddr, path::PathBuf, sync::OnceLock};

use eyre::Result;
use ipnet::IpNet;
use serde::{Deserialize, Serialize};
use serde_json::Value;

static DEFAULT_CONFIG: &str = include_str!("../../../authentik/lib/default.yml");
static CONFIG: OnceLock<Config> = OnceLock::new();

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub postgresql: PostgreSQLConfig,

    pub listen: ListenConfig,

    pub http_timeout: u32,

    pub debug: bool,

    pub log: Option<String>,
    pub log_level: String,

    pub error_reporting: ErrorReportingConfig,

    pub outposts: OutpostsConfig,

    pub cookie_domain: Option<String>,

    pub compliance: ComplianceConfig,

    pub blueprints_dir: PathBuf,
    pub cert_discovery_dir: PathBuf,

    pub web: WebConfig,

    pub worker: WorkerConfig,

    // Outpost specific config
    // These are only relevant for outposts, and cannot be set via YAML
    // They are loaded via this config loader to support file:// schemas
    pub authentik_host: Option<String>,
    pub authentik_host_browser: Option<String>,
    pub authentik_token: Option<String>,
    pub authentik_insecure: Option<bool>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PostgreSQLConfig {
    pub host: String,
    pub port: u16,
    pub user: String,
    pub password: String,
    pub name: String,

    pub sslmode: String,
    pub sslrootcert: Option<String>,
    pub sslcert: Option<String>,
    pub sslkey: Option<String>,

    pub default_schema: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ListenConfig {
    pub http: Vec<SocketAddr>,
    pub https: Vec<SocketAddr>,
    pub ldap: Vec<SocketAddr>,
    pub ldaps: Vec<SocketAddr>,
    pub radius: Vec<SocketAddr>,
    pub metrics: Vec<SocketAddr>,
    pub trusted_proxy_cidrs: Vec<IpNet>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorReportingConfig {
    pub enabled: bool,
    pub sentry_dsn: Option<String>,
    pub environment: String,
    pub send_pii: bool,
    pub sample_rate: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OutpostsConfig {
    pub disable_embedded_outpost: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LDAPConfig {
    pub task_timeout_hours: u32,
    pub page_size: u32,
    pub tls: LDAPTLSConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LDAPTLSConfig {
    pub ciphers: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ComplianceConfig {
    pub fips: ComplianceFipsConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ComplianceFipsConfig {
    pub enabled: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WebConfig {
    pub workers: Option<u32>,
    pub threads: u32,
    pub path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkerConfig {
    pub processes: u32,
    pub threads: u32,
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

    fn load_raw() -> Result<Value> {
        let mut builder = config::Config::builder();
        builder = builder.add_source(config::File::from_str(
            DEFAULT_CONFIG,
            config::FileFormat::Yaml,
        ));
        for path in Self::config_paths() {
            builder = builder.add_source(config::File::from(path));
        }
        builder = builder.add_source(config::Environment::with_prefix("AUTHENTIK"));
        let config = builder.build()?;
        let raw = config.try_deserialize::<Value>()?;
        Ok(raw)
    }

    fn expand_value(value: &str) -> Result<String> {
        let trimmed = value.trim();
        let value = if let Some(path) = trimmed.strip_prefix("file://") {
            fs::read_to_string(path).map(|s| s.trim().to_owned())?
        } else if let Some(env_var) = trimmed.strip_prefix("env://") {
            env::var(env_var)?
        } else {
            value.to_owned()
        };
        Ok(value)
    }

    fn expand(mut raw: Value) -> Value {
        match &mut raw {
            Value::String(s) => {
                if let Ok(expanded) = Self::expand_value(s) {
                    Value::String(expanded)
                } else {
                    raw
                }
            }
            Value::Array(arr) => {
                Value::Array(arr.iter().map(|v| Self::expand(v.clone())).collect())
            }
            Value::Object(map) => Value::Object(
                map.iter()
                    .map(|(k, v)| (k.clone(), Self::expand(v.clone())))
                    .collect(),
            ),
            _ => raw,
        }
    }

    fn load() -> Result<Self> {
        let raw = Self::load_raw()?;
        let expanded = Self::expand(raw);
        let config: Config = serde_json::from_value(expanded)?;
        Ok(config)
    }

    pub fn setup() -> Result<()> {
        let config = Self::load()?;
        CONFIG.get_or_init(|| config);
        Ok(())
    }
}

pub fn get_config() -> &'static Config {
    CONFIG.get_or_init(|| Config::load().unwrap())
}
