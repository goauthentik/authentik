//! Unauthenticated-path allowlist (`skip_path_regex`).

use ak_client::models::ProxyMode;
use regex::Regex;
use tracing::warn;
use url::Url;

use crate::outpost::proxy::application::Application;

/// Compile the newline-separated `skip_path_regex` config, skipping blank lines
/// and patterns that fail to compile.
pub(crate) fn compile_skip_regex(skip_path_regex: Option<&str>) -> Vec<Regex> {
    skip_path_regex
        .into_iter()
        .flat_map(|raw| raw.split('\n'))
        .filter(|pattern| !pattern.is_empty())
        .filter_map(|pattern| {
            Regex::new(pattern)
                .inspect_err(|err| warn!(?err, pattern, "failed to compile skip_path_regex"))
                .ok()
        })
        .collect()
}

/// The string an allowlist pattern is tested against: the path for
/// proxy/`forward_single`, the full URL for `forward_domain`.
fn allowlist_target<'a>(mode: ProxyMode, path: &'a str, full: &'a str) -> &'a str {
    match mode {
        ProxyMode::Proxy | ProxyMode::ForwardSingle => path,
        ProxyMode::ForwardDomain => full,
    }
}

/// Whether `url` matches any allowlist pattern. Proxy/`forward_single` match on
/// the path; `forward_domain` matches the full URL.
pub(crate) fn is_allowlisted(regexes: &[Regex], mode: ProxyMode, url: &Url) -> bool {
    is_allowlisted_target(regexes, mode, url.path(), url.as_str())
}

/// As [`is_allowlisted`], but for a forward target supplied as a path and a
/// full, possibly scheme-less, URL string (the envoy handler reconstructs a
/// scheme-less target that cannot be a `Url`).
pub(crate) fn is_allowlisted_target(
    regexes: &[Regex],
    mode: ProxyMode,
    path: &str,
    full: &str,
) -> bool {
    let target = allowlist_target(mode, path, full);
    regexes.iter().any(|regex| regex.is_match(target))
}

impl Application {
    /// Whether the request URL is exempt from authentication.
    pub(super) fn is_allowlisted(&self, url: &Url) -> bool {
        self.provider
            .mode
            .is_some_and(|mode| is_allowlisted(&self.unauthenticated_regex, mode, url))
    }

    /// Allowlist check for a forward target supplied as a path and a full,
    /// possibly scheme-less, URL string — used by the envoy handler.
    pub(super) fn is_allowlisted_target(&self, path: &str, full: &str) -> bool {
        self.provider.mode.is_some_and(|mode| {
            is_allowlisted_target(&self.unauthenticated_regex, mode, path, full)
        })
    }
}

#[cfg(test)]
mod tests {
    use ak_client::models::ProxyMode;
    use url::Url;

    use super::{compile_skip_regex, is_allowlisted, is_allowlisted_target};

    #[test]
    fn compiles_and_skips_invalid() {
        let regexes = compile_skip_regex(Some("/skip.*\n\n/health\n["));
        // Two valid patterns; the blank line and "[" are dropped.
        assert_eq!(regexes.len(), 2);
        assert!(compile_skip_regex(None).is_empty());
        assert!(compile_skip_regex(Some("")).is_empty());
    }

    #[test]
    fn proxy_matches_on_path() {
        let regexes = compile_skip_regex(Some("/skip.*"));
        let allowed = Url::parse("https://app.example.com/skip/here").expect("url");
        let denied = Url::parse("https://app.example.com/private").expect("url");

        assert!(is_allowlisted(&regexes, ProxyMode::Proxy, &allowed));
        assert!(!is_allowlisted(&regexes, ProxyMode::Proxy, &denied));
    }

    #[test]
    fn forward_domain_matches_on_full_url() {
        let regexes = compile_skip_regex(Some("^https://public\\.example\\.com/"));
        let allowed = Url::parse("https://public.example.com/anything").expect("url");
        let denied = Url::parse("https://private.example.com/anything").expect("url");

        assert!(is_allowlisted(&regexes, ProxyMode::ForwardDomain, &allowed));
        assert!(!is_allowlisted(&regexes, ProxyMode::ForwardDomain, &denied));
    }

    #[test]
    fn forward_domain_matches_scheme_less_target() {
        // The envoy handler reconstructs a scheme-less target (`//host/path`).
        // A host-anchored pattern still matches without a scheme.
        let regexes = compile_skip_regex(Some("^//public\\.example\\.com/"));
        assert!(is_allowlisted_target(
            &regexes,
            ProxyMode::ForwardDomain,
            "/info",
            "//public.example.com/info"
        ));
        assert!(!is_allowlisted_target(
            &regexes,
            ProxyMode::ForwardDomain,
            "/info",
            "//private.example.com/info"
        ));
    }
}
