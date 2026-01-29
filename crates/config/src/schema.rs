use std::{net::SocketAddr, path::PathBuf};

use ipnet::IpNet;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub postgresql: PostgreSQLConfig,

    pub listen: ListenConfig,

    pub http_timeout: u32,

    pub debug: bool,

    pub log_level: String,
    pub log: LogConfig,

    pub error_reporting: ErrorReportingConfig,

    pub outposts: OutpostsConfig,

    pub cookie_domain: Option<String>,

    pub compliance: ComplianceConfig,

    pub blueprints_dir: PathBuf,
    pub cert_discovery_dir: PathBuf,

    pub web: WebConfig,

    pub worker: WorkerConfig,

    pub storage: StorageConfig,

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

    pub conn_max_age: Option<u64>,
    pub conn_health_checks: bool,

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
    pub debug: SocketAddr,
    pub trusted_proxy_cidrs: Vec<IpNet>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LogConfig {
    pub http_headers: Vec<String>,
    pub rust_log: Option<String>,
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
    pub workers: usize,
    pub threads: usize,
    pub path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkerConfig {
    pub processes: u32,
    pub threads: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StorageConfig {
    pub backend: String,
    pub file: StorageFileConfig,
    pub media: Option<StorageOverrideConfig>,
    pub reports: Option<StorageOverrideConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StorageFileConfig {
    pub path: PathBuf,
}

#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub struct StorageOverrideConfig {
    pub backend: Option<String>,
    pub file: Option<StorageFileOverrideConfig>,
}

#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub struct StorageFileOverrideConfig {
    pub path: Option<PathBuf>,
}
