use std::{collections::HashMap, net::SocketAddr, num::NonZeroUsize, path::PathBuf};

use ipnet::IpNet;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub(crate) struct Config {
    pub(crate) postgresql: PostgreSQLConfig,

    pub(crate) listen: ListenConfig,

    pub(crate) http_timeout: u32,

    pub(crate) debug: bool,
    #[serde(default)]
    pub(crate) secret_key: String,

    pub(crate) log_level: String,
    pub(crate) log: LogConfig,

    pub(crate) error_reporting: ErrorReportingConfig,

    pub(crate) outposts: OutpostsConfig,

    pub(crate) cookie_domain: Option<String>,

    pub(crate) compliance: ComplianceConfig,

    pub(crate) blueprints_dir: PathBuf,
    pub(crate) cert_discovery_dir: PathBuf,

    pub(crate) web: WebConfig,

    pub(crate) worker: WorkerConfig,

    pub(crate) storage: StorageConfig,

    // Outpost specific config
    // These are only relevant for outposts, and cannot be set via YAML
    // They are loaded via this config loader to support file:// schemas
    pub(crate) authentik_host: Option<String>,
    pub(crate) authentik_host_browser: Option<String>,
    pub(crate) authentik_token: Option<String>,
    pub(crate) authentik_insecure: Option<bool>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub(crate) struct PostgreSQLConfig {
    pub(crate) host: String,
    pub(crate) port: u16,
    pub(crate) user: String,
    pub(crate) password: String,
    pub(crate) name: String,

    pub(crate) sslmode: String,
    pub(crate) sslrootcert: Option<String>,
    pub(crate) sslcert: Option<String>,
    pub(crate) sslkey: Option<String>,

    pub(crate) conn_max_age: Option<u64>,
    pub(crate) conn_health_checks: bool,

    pub(crate) default_schema: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub(crate) struct ListenConfig {
    pub(crate) http: Vec<SocketAddr>,
    pub(crate) https: Vec<SocketAddr>,
    pub(crate) ldap: Vec<SocketAddr>,
    pub(crate) ldaps: Vec<SocketAddr>,
    pub(crate) radius: Vec<SocketAddr>,
    pub(crate) metrics: Vec<SocketAddr>,
    pub(crate) debug: SocketAddr,
    pub(crate) trusted_proxy_cidrs: Vec<IpNet>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub(crate) struct LogConfig {
    pub(crate) http_headers: Vec<String>,
    pub(crate) rust_log: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub(crate) struct ErrorReportingConfig {
    pub(crate) enabled: bool,
    pub(crate) sentry_dsn: Option<String>,
    pub(crate) environment: String,
    pub(crate) send_pii: bool,
    pub(crate) sample_rate: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub(crate) struct OutpostsConfig {
    pub(crate) disable_embedded_outpost: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub(crate) struct ComplianceConfig {
    pub(crate) fips: ComplianceFipsConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub(crate) struct ComplianceFipsConfig {
    pub(crate) enabled: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub(crate) struct WebConfig {
    pub(crate) workers: usize,
    pub(crate) threads: usize,
    pub(crate) path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub(crate) struct WorkerConfig {
    pub(crate) processes: NonZeroUsize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub(crate) struct StorageConfig {
    pub(crate) backend: String,
    pub(crate) file: StorageFileConfig,
    pub(crate) media: Option<StorageOverrideConfig>,
    pub(crate) reports: Option<StorageOverrideConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub(crate) struct StorageFileConfig {
    pub(crate) path: PathBuf,
}

#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub(crate) struct StorageOverrideConfig {
    pub(crate) backend: Option<String>,
    pub(crate) file: Option<StorageFileOverrideConfig>,
}

#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub(crate) struct StorageFileOverrideConfig {
    pub(crate) path: Option<PathBuf>,
}
