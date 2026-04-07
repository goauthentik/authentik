//! Various utilities used by other crates

pub mod arbiter;
pub use arbiter::{Arbiter, Event, Tasks};
pub mod config;
pub mod mode;
pub use mode::Mode;
pub mod tls;
pub mod tokio;
pub mod tracing;

pub const VERSION: &str = env!("CARGO_PKG_VERSION");

pub fn authentik_build_hash(fallback: Option<String>) -> String {
    std::env::var("GIT_BUILD_HASH").unwrap_or_else(|_| fallback.unwrap_or_default())
}

pub fn authentik_full_version() -> String {
    let build_hash = authentik_build_hash(None);
    if build_hash.is_empty() {
        VERSION.to_owned()
    } else {
        format!("{VERSION}+{build_hash}")
    }
}

pub fn authentik_user_agent() -> String {
    format!("authentik@{}", authentik_full_version())
}
