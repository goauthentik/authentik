pub mod arbiter;
pub mod axum;
pub mod config;
#[cfg(feature = "core")]
pub mod db;
pub mod metrics;
pub mod mode;
#[cfg(feature = "core")]
pub mod server;
pub mod tracing;
#[cfg(feature = "core")]
pub mod worker;

const VERSION: &str = env!("CARGO_PKG_VERSION");

pub(crate) fn authentik_build_hash(fallback: Option<String>) -> String {
    std::env::var("GIT_BUILD_HASH").unwrap_or_else(|_| fallback.unwrap_or_default())
}

pub(crate) fn authentik_full_version() -> String {
    let build_hash = authentik_build_hash(None);
    if build_hash.is_empty() {
        VERSION.to_owned()
    } else {
        format!("{VERSION}+{build_hash}")
    }
}

pub(crate) fn authentik_user_agent() -> String {
    format!("authentik@{}", authentik_full_version())
}
