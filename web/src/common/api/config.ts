import {
    CSRFMiddleware,
    EventMiddleware,
    LocaleMiddleware,
    LoggingMiddleware,
} from "#common/api/middleware";
import { globalAK } from "#common/global";
import { SentryMiddleware } from "#common/sentry/middleware";

import { Config, Configuration, CurrentBrand, RootApi } from "@goauthentik/api";

let globalConfigPromise: Promise<Config> | undefined = Promise.resolve(globalAK().config);
export function config(): Promise<Config> {
    if (!globalConfigPromise) {
        globalConfigPromise = new RootApi(DEFAULT_CONFIG).rootConfigRetrieve();
    }
    return globalConfigPromise;
}

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

export const DEFAULT_CONFIG = new Configuration({
    basePath: `${globalAK().api.base}api/v3`,
    middleware: [
        new CSRFMiddleware(),
        new EventMiddleware(),
        new LoggingMiddleware(globalAK().brand),
        new SentryMiddleware(),
        new LocaleMiddleware(),
    ],
});

// This is just a function so eslint doesn't complain about
// missing-whitespace-between-attributes or
// unexpected-character-in-attribute-name
export function AndNext(url: string): string {
    return `?next=${encodeURIComponent(url)}`;
}

console.debug(
    `authentik(early): version ${import.meta.env.AK_VERSION}, apiBase ${DEFAULT_CONFIG.basePath}`,
);
