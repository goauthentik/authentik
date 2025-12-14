import {
    CSRFMiddleware,
    EventMiddleware,
    LocaleMiddleware,
    LoggingMiddleware,
} from "#common/api/middleware";
import { globalAK } from "#common/global";
import { SentryMiddleware } from "#common/sentry/middleware";

import { Configuration, CurrentBrand } from "@goauthentik/api";

const { locale, api, brand } = globalAK();

export const DEFAULT_CONFIG = new Configuration({
    basePath: `${api.base}api/v3`,
    middleware: [
        new CSRFMiddleware(),
        new EventMiddleware(),
        new LoggingMiddleware(brand),
        new SentryMiddleware(),
        new LocaleMiddleware(locale),
    ],
});

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

// This is just a function so eslint doesn't complain about
// missing-whitespace-between-attributes or
// unexpected-character-in-attribute-name
export function AndNext(url: string): string {
    return `?next=${encodeURIComponent(url)}`;
}

console.debug(
    `authentik(early): version ${import.meta.env.AK_VERSION}, apiBase ${DEFAULT_CONFIG.basePath}`,
);
