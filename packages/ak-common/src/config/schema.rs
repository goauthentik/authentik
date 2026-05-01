use std::{collections::HashMap, net::SocketAddr, num::NonZeroUsize};

use ipnet::IpNet;
use serde::{Deserialize, Serialize};

pub(super) const KEYS_TO_PARSE_AS_LIST: [&str; 4] = [
    "listen.http",
    "listen.metrics",
    "listen.trusted_proxy_cidrs",
    "log.http_headers",
];

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub postgresql: PostgreSQLConfig,

    pub listen: ListenConfig,

    pub debug: bool,
    #[serde(default)]
    pub secret_key: String,

    pub log_level: String,
    pub log: LogConfig,

    pub error_reporting: ErrorReportingConfig,

    pub compliance: ComplianceConfig,

    pub web: WebConfig,

    pub worker: WorkerConfig,

    // Outpost specific fields
    pub host: Option<String>,
    pub token: Option<String>,
    pub insecure: Option<bool>,
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
    pub metrics: Vec<SocketAddr>,
    pub debug_tokio: SocketAddr,
    pub trusted_proxy_cidrs: Vec<IpNet>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LogConfig {
    pub http_headers: Vec<String>,
    pub rust_log: HashMap<String, String>,
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
pub struct ComplianceConfig {
    pub fips: ComplianceFipsConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ComplianceFipsConfig {
    pub enabled: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WebConfig {
    pub path: String,
    pub timeout_http_read_header: String,
    pub timeout_http_read: String,
    pub timeout_http_write: String,
    pub timeout_http_idle: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkerConfig {
    pub processes: NonZeroUsize,
}
