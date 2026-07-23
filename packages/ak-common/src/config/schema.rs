use std::{collections::HashMap, net::SocketAddr, num::NonZeroUsize, path::PathBuf};

use ipnet::IpNet;
use serde::{Deserialize, Deserializer, Serialize, de::Error as _};

pub(super) const KEYS_TO_PARSE_AS_LIST: [&str; 5] = [
    "listen.http",
    "listen.https",
    "listen.metrics",
    "listen.trusted_proxy_cidrs",
    "log.http_headers",
];

fn deserialize_optional_u64<'de, D>(deserializer: D) -> Result<Option<u64>, D::Error>
where
    D: Deserializer<'de>,
{
    // The value comes as a number from config files but as a string from env vars.
    #[derive(Deserialize)]
    #[serde(untagged)]
    enum NumOrStr {
        Num(u64),
        Str(String),
    }

    match Option::<NumOrStr>::deserialize(deserializer)? {
        None => Ok(None),
        Some(NumOrStr::Num(n)) => Ok(Some(n)),
        Some(NumOrStr::Str(s)) => {
            let s = s.trim();
            if s.is_empty() || s.eq_ignore_ascii_case("none") || s.eq_ignore_ascii_case("null") {
                Ok(None)
            } else {
                s.parse().map(Some).map_err(D::Error::custom)
            }
        }
    }
}

mod sealed {
    use std::{fmt::Display, str::FromStr};

    /// Numeric config types that may be provided either as a native number (YAML / environment
    /// variables) or as a string (from `file://` / `env://` references, which resolve to strings).
    ///
    /// Sealed so [`super::deserialize_str_or_num`] can only be attached to numeric fields:
    /// applying it to a `String` field would silently coerce values that must stay strings (e.g. an
    /// all-digit password read from a file), which is a compile error instead.
    pub(super) trait Numeric: FromStr<Err: Display> {}

    impl Numeric for u16 {}
    impl Numeric for u64 {}
    impl Numeric for f32 {}
    impl Numeric for std::num::NonZeroUsize {}
}

/// Deserialize a numeric field that may arrive as a number or as a string.
///
/// YAML numbers and environment variables (coerced by `config_rs`) arrive already typed; `file://`
/// and `env://` references resolve to strings and are parsed here. Because this is opt-in per
/// field, string-typed fields keep their raw value and are never coerced.
fn deserialize_str_or_num<'de, D, T>(deserializer: D) -> Result<T, D::Error>
where
    D: Deserializer<'de>,
    T: Deserialize<'de> + sealed::Numeric,
{
    #[derive(Deserialize)]
    #[serde(untagged)]
    enum NumOrStr<T> {
        Num(T),
        Str(String),
    }

    match NumOrStr::<T>::deserialize(deserializer)? {
        NumOrStr::Num(n) => Ok(n),
        NumOrStr::Str(s) => s.trim().parse().map_err(D::Error::custom),
    }
}

/// Deserialize a boolean that may arrive as a native bool or as a string (`"true"`/`"false"`,
/// case-insensitive), for the same `file://` / `env://` reason as [`deserialize_str_or_num`].
fn deserialize_str_or_bool<'de, D>(deserializer: D) -> Result<bool, D::Error>
where
    D: Deserializer<'de>,
{
    #[derive(Deserialize)]
    #[serde(untagged)]
    enum BoolOrStr {
        Bool(bool),
        Str(String),
    }

    match BoolOrStr::deserialize(deserializer)? {
        BoolOrStr::Bool(b) => Ok(b),
        BoolOrStr::Str(s) => s
            .trim()
            .to_ascii_lowercase()
            .parse()
            .map_err(D::Error::custom),
    }
}

/// Like [`deserialize_str_or_bool`] but for optional booleans.
fn deserialize_optional_str_or_bool<'de, D>(deserializer: D) -> Result<Option<bool>, D::Error>
where
    D: Deserializer<'de>,
{
    #[derive(Deserialize)]
    #[serde(untagged)]
    enum BoolOrStr {
        Bool(bool),
        Str(String),
    }

    Ok(match Option::<BoolOrStr>::deserialize(deserializer)? {
        None => None,
        Some(BoolOrStr::Bool(b)) => Some(b),
        Some(BoolOrStr::Str(s)) => Some(
            s.trim()
                .to_ascii_lowercase()
                .parse()
                .map_err(D::Error::custom)?,
        ),
    })
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub postgresql: PostgreSQLConfig,

    pub listen: ListenConfig,

    #[serde(deserialize_with = "deserialize_str_or_bool")]
    pub debug: bool,
    #[serde(default)]
    pub secret_key: String,

    pub log_level: String,
    pub log: LogConfig,

    pub error_reporting: ErrorReportingConfig,

    pub compliance: ComplianceConfig,

    pub web: WebConfig,

    pub worker: WorkerConfig,

    pub storage: StorageConfig,

    // Outpost specific fields
    pub host: Option<String>,
    pub host_browser: Option<String>,
    pub token: Option<String>,
    #[serde(default, deserialize_with = "deserialize_optional_str_or_bool")]
    pub insecure: Option<bool>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PostgreSQLConfig {
    pub host: String,
    #[serde(deserialize_with = "deserialize_str_or_num")]
    pub port: u16,
    pub user: String,
    pub password: String,
    pub name: String,

    pub sslmode: String,
    pub sslrootcert: Option<String>,
    pub sslcert: Option<String>,
    pub sslkey: Option<String>,

    #[serde(deserialize_with = "deserialize_optional_u64")]
    pub conn_max_age: Option<u64>,
    #[serde(deserialize_with = "deserialize_str_or_bool")]
    pub conn_health_checks: bool,

    pub default_schema: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ListenConfig {
    pub http: Vec<SocketAddr>,
    pub https: Vec<SocketAddr>,
    pub metrics: Vec<SocketAddr>,
    pub debug_tokio: Option<SocketAddr>,
    pub trusted_proxy_cidrs: Vec<IpNet>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LogConfig {
    pub http_headers: Vec<String>,
    pub rust_log: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorReportingConfig {
    #[serde(deserialize_with = "deserialize_str_or_bool")]
    pub enabled: bool,
    pub sentry_dsn: Option<String>,
    pub environment: String,
    #[serde(deserialize_with = "deserialize_str_or_bool")]
    pub send_pii: bool,
    #[serde(deserialize_with = "deserialize_str_or_num")]
    pub sample_rate: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ComplianceConfig {
    pub fips: ComplianceFipsConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ComplianceFipsConfig {
    #[serde(deserialize_with = "deserialize_str_or_bool")]
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
    #[serde(deserialize_with = "deserialize_str_or_num")]
    pub processes: NonZeroUsize,
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
