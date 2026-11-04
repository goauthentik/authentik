"""CIMD metrics. Labels are small fixed sets, never client IDs or URLs."""

from prometheus_client import Counter, Histogram

HIST_CIMD_FETCH = Histogram(
    "authentik_enterprise_oauth2_cimd_fetch_duration_seconds",
    "Duration of CIMD metadata and JWKS fetches, including validation.",
    ["kind", "outcome"],
)
COUNTER_CIMD_CACHE = Counter(
    "authentik_enterprise_oauth2_cimd_cache_lookups",
    "CIMD metadata and JWKS cache lookups.",
    ["kind", "result"],
)
COUNTER_CIMD_RESOLVE = Counter(
    "authentik_enterprise_oauth2_cimd_resolutions",
    "CIMD client resolutions.",
    ["profile", "outcome"],
)
