use std::{
    env, fs,
    net::SocketAddr,
    path::{Path, PathBuf},
    sync::OnceLock,
};

use color_eyre::eyre::Result;
use serde::{Deserialize, Serialize};
use serde_json::Value;

static DEFAULT_CONFIG: &str = include_str!("../../../authentik/lib/default.yml");
static CONFIG: OnceLock<Config> = OnceLock::new();

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub postgresql: PostgreSQLConfig,

    pub listen: ListenConfig,

    pub http_timeout: u32,

    pub cache: CacheConfig,

    pub debug: bool,
    pub debugger: bool,

    pub log_level: String,

    pub sessions: SessionsConfig,

    pub error_reporting: ErrorReportingConfig,

    pub email: EmailConfig,

    pub throttle: ThrottleConfig,

    pub outposts: OutpostsConfig,

    pub ldap: LDAPConfig,

    pub sources: SourcesConfig,

    pub reputation: ReputationConfig,

    pub cookie_domain: Option<String>,

    pub disable_update_check: bool,
    pub disable_startup_analytics: bool,

    pub events: EventsConfig,

    pub compliance: ComplianceConfig,

    pub blueprints_dir: PathBuf,
    pub cert_discovery_dir: PathBuf,

    pub tenants: TenantsConfig,

    pub web: WebConfig,

    pub worker: WorkerConfig,

    pub storage: StorageConfig,

    // Outpost specific config
    // These are only relevant for outposts, and cannot be set via YAML
    // They are loaded via this config loader to support file:// schemas
    pub authentik_host: String,
    pub authentik_host_browser: String,
    pub authentik_token: String,
    pub authentik_insecure: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PostgreSQLConfig {
    pub host: String,
    pub port: u16,
    pub user: String,
    pub password: String,
    pub name: String,

    pub sslmode: String,
    pub sslrootcert: String,
    pub sslcert: String,
    pub sslkey: String,

    pub use_pool: bool,
    pub pool_options: Value,

    pub conn_options: Value,
    pub conn_max_age: u32,
    pub conn_health_checks: bool,
    pub disable_server_side_cursors: bool,

    pub default_schema: String,

    // TODO: read replicas
    pub test: PostgreSQLTestConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PostgreSQLTestConfig {
    pub name: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ListenConfig {
    pub http: Vec<SocketAddr>,
    pub https: Vec<SocketAddr>,
    pub ldap: Vec<SocketAddr>,
    pub ldaps: Vec<SocketAddr>,
    pub radius: Vec<SocketAddr>,
    pub metrics: Vec<SocketAddr>,
    pub debug: Vec<SocketAddr>,
    pub debug_py: Vec<SocketAddr>,
    // TODO: subnet type
    pub trusted_proxy_cidrs: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CacheConfig {
    pub timeout: u32,
    pub timeout_flows: u32,
    pub timeout_policies: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionsConfig {
    pub unauthenticated_age: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorReportingConfig {
    pub enabled: bool,
    pub sentry_dsn: String,
    pub environment: String,
    pub send_pii: bool,
    pub sample_rate: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EmailConfig {
    pub host: String,
    pub port: u16,
    pub username: String,
    pub password: String,
    pub use_tls: bool,
    pub use_ssl: bool,
    pub timeout: u32,
    pub from: String,
    pub template_dir: PathBuf,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ThrottleConfig {
    pub providers: ThrottleProvidersConfig,
    pub default: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ThrottleProvidersConfig {
    pub oauth2: ThrottleProvidersOAuth2Config,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ThrottleProvidersOAuth2Config {
    pub device: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OutpostsConfig {
    pub container_image_base: String,
    pub discover: bool,
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
pub struct SourcesConfig {
    pub kerberos: SourcesKerberosConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SourcesKerberosConfig {
    pub task_timeout_hours: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReputationConfig {
    pub expiry: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EventsConfig {
    pub context_processors: EventsContextProcessorsConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EventsContextProcessorsConfig {
    pub geoip: PathBuf,
    pub asn: PathBuf,
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
pub struct TenantsConfig {
    pub enabled: bool,
    pub api_key: String,
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
    pub consumer_listen_timeout: String,
    pub task_max_retries: u32,
    pub task_default_time_limit: String,
    pub task_purge_interval: String,
    pub task_expiration: String,
    pub scheduler_interval: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StorageConfig {
    pub backend: String,
    pub file: StorageFileConfig,
    pub s3: StorageS3Config,
    pub media: StorageMediaConfig,
    pub reports: StorageReportsConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StorageFileConfig {
    pub path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StorageS3Config {
    #[serde(default)]
    pub region: Option<String>,
    pub use_ssl: bool,
    #[serde(default)]
    pub endpoint: Option<String>,
    #[serde(default)]
    pub access_key: Option<String>,
    #[serde(default)]
    pub secret_key: Option<String>,
    pub bucket_name: String,
    #[serde(default)]
    pub custom_domain: Option<String>,
    pub secure_urls: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StorageMediaConfig {
    pub backend: String,
    pub file: StorageFileConfig,
    pub s3: StorageS3Config,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StorageReportsConfig {
    pub backend: String,
    pub file: StorageFileConfig,
    pub s3: StorageS3Config,
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
