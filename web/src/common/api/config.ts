import {
    CSRFHeaderName,
    CSRFMiddleware,
    EventMiddleware,
    LoggingMiddleware,
} from "@goauthentik/common/api/middleware";
import { EVENT_LOCALE_REQUEST, VERSION } from "@goauthentik/common/constants";
import { ServerContext } from "@goauthentik/common/server-context";

import { Configuration, CurrentBrand } from "@goauthentik/api";

// HACK: Workaround for ESBuild not being able to hoist import statement across entrypoints.
// This can be removed after ESBuild uses a single build context for all entrypoints.
export { CSRFHeaderName };

export function brandSetFavicon(brand: CurrentBrand) {
    /**
     *  <link rel="icon" href="/static/dist/assets/icons/icon.png">
     *  <link rel="shortcut icon" href="/static/dist/assets/icons/icon.png">
     */
    const rels = ["icon", "shortcut icon"];
    rels.forEach((rel) => {
        let relIcon = document.head.querySelector<HTMLLinkElement>(`link[rel='${rel}']`);
        if (!relIcon) {
            relIcon = document.createElement("link");
            relIcon.rel = rel;
            document.getElementsByTagName("head")[0].appendChild(relIcon);
        }
        relIcon.href = brand.brandingFavicon;
    });
}

export function brandSetLocale(brand: CurrentBrand) {
    if (brand.defaultLocale === "") {
        return;
    }
    console.debug("authentik/locale: setting locale from brand default");
    window.dispatchEvent(
        new CustomEvent(EVENT_LOCALE_REQUEST, {
            composed: true,
            bubbles: true,
            detail: { locale: brand.defaultLocale },
        }),
    );
}

export function getMetaContent(key: string): string {
    const metaEl = document.querySelector<HTMLMetaElement>(`meta[name=${key}]`);
    if (!metaEl) return "";

    return metaEl.content;
}

export const DEFAULT_CONFIG = new Configuration({
    basePath: `${ServerContext.baseURL}api/v3`,
    headers: {
        "sentry-trace": ServerContext.sentryTrace,
    },
    middleware: [
        new CSRFMiddleware(),
        new EventMiddleware(),
        new LoggingMiddleware(ServerContext.brand),
    ],
});

// This is just a function so eslint doesn't complain about
// missing-whitespace-between-attributes or
// unexpected-character-in-attribute-name
export function AndNext(url: string): string {
    return `?next=${encodeURIComponent(url)}`;
}

console.debug(`authentik(early): version ${VERSION}, apiBase ${DEFAULT_CONFIG.basePath}`);
