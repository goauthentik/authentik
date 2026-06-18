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

/// Whether `url` matches any allowlist pattern. Proxy/forward_single match on the
/// path; forward_domain matches the full URL.
pub(crate) fn is_allowlisted(regexes: &[Regex], mode: ProxyMode, url: &Url) -> bool {
    let test = match mode {
        ProxyMode::Proxy | ProxyMode::ForwardSingle => url.path(),
        ProxyMode::ForwardDomain => url.as_str(),
    };
    regexes.iter().any(|regex| regex.is_match(test))
}

impl Application {
    /// Whether the request URL is exempt from authentication.
    pub(super) fn is_allowlisted(&self, url: &Url) -> bool {
        self.provider
            .mode
            .is_some_and(|mode| is_allowlisted(&self.unauthenticated_regex, mode, url))
    }
}

#[cfg(test)]
mod tests {
    use ak_client::models::ProxyMode;
    use url::Url;

    use super::{compile_skip_regex, is_allowlisted};

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
}
