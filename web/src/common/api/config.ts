import {
    CSRFMiddleware,
    EventMiddleware,
    LoggingMiddleware,
} from "@goauthentik/common/api/middleware";
import { VERSION } from "@goauthentik/common/constants";
import { APIConfig, BrandConfig } from "@goauthentik/common/global";

import { Configuration as ApiConfiguration } from "@goauthentik/api";

/**
 * Extract the content of a meta tag by name.
 *
 * @todo Can we memoize this?
 */
function extractMetaContent(name: string): string {
    const metaEl = document.querySelector<HTMLMetaElement>(`meta[name=${name}]`);

    if (!metaEl) return "";

    return metaEl.content;
}

/**
 * Default API Configuration.
 *
 * @todo This is a frequent source of duplication when working with the API.
 * We should consider moving this to a more central location.
 */
export const DEFAULT_CONFIG = new ApiConfiguration({
    basePath: `${APIConfig.base}api/v3`,
    headers: {
        "sentry-trace": extractMetaContent("sentry-trace"),
    },
    middleware: [
        // ---
        new CSRFMiddleware(),
        new EventMiddleware(),
        new LoggingMiddleware(BrandConfig),
    ],
});

// This is just a function so eslint doesn't complain about
// missing-whitespace-between-attributes or
// unexpected-character-in-attribute-name
export function AndNext(url: string): string {
    return `?next=${encodeURIComponent(url)}`;
}

console.debug(`authentik(early): version ${VERSION}, apiBase ${DEFAULT_CONFIG.basePath}`);
