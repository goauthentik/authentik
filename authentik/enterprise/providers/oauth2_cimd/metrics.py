"""CIMD metrics. Labels are small fixed sets, never client IDs or URLs."""

from prometheus_client import Counter, Histogram

HIST_CIMD_FETCH = Histogram(
    "authentik_enterprise_oauth2_cimd_fetch_duration_seconds",
    "Duration of CIMD metadata fetches, including validation.",
    ["outcome"],
)
COUNTER_CIMD_CACHE = Counter(
    "authentik_enterprise_oauth2_cimd_cache_lookups",
    "CIMD metadata cache lookups.",
    ["result"],
)
COUNTER_CIMD_RESOLVE = Counter(
    "authentik_enterprise_oauth2_cimd_resolutions",
    "CIMD public client resolutions.",
    ["outcome"],
)
