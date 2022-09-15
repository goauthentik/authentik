import {
    CSRFMiddleware,
    EventMiddleware,
    LoggingMiddleware,
} from "@goauthentik/common/api/middleware";
import { EVENT_REFRESH, VERSION } from "@goauthentik/common/constants";
import { globalAK } from "@goauthentik/common/global";
import { activateLocale } from "@goauthentik/common/ui/locale";

import {
    Config,
    ConfigFromJSON,
    Configuration,
    CoreApi,
    CurrentTenant,
    CurrentTenantFromJSON,
    RootApi,
} from "@goauthentik/api";

let globalConfigPromise: Promise<Config> | undefined = Promise.resolve(
    ConfigFromJSON(globalAK()?.config),
);
export function config(): Promise<Config> {
    if (!globalConfigPromise) {
        globalConfigPromise = new RootApi(DEFAULT_CONFIG).rootConfigRetrieve();
    }
    return globalConfigPromise;
}

export function tenantSetFavicon(tenant: CurrentTenant) {
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
        relIcon.href = tenant.brandingFavicon;
    });
}

export function tenantSetLocale(tenant: CurrentTenant) {
    if (tenant.defaultLocale === "") {
        return;
    }
    console.debug("authentik/locale: setting locale from tenant default");
    activateLocale(tenant.defaultLocale);
}

let globalTenantPromise: Promise<CurrentTenant> | undefined = Promise.resolve(
    CurrentTenantFromJSON(globalAK()?.tenant),
);
export function tenant(): Promise<CurrentTenant> {
    if (!globalTenantPromise) {
        globalTenantPromise = new CoreApi(DEFAULT_CONFIG)
            .coreTenantsCurrentRetrieve()
            .then((tenant) => {
                tenantSetFavicon(tenant);
                tenantSetLocale(tenant);
                return tenant;
            });
    }
    return globalTenantPromise;
}

export function getMetaContent(key: string): string {
    const metaEl = document.querySelector<HTMLMetaElement>(`meta[name=${key}]`);
    if (!metaEl) return "";
    return metaEl.content;
}

export const DEFAULT_CONFIG = new Configuration({
    basePath: process.env.AK_API_BASE_PATH + "/api/v3",
    headers: {
        "sentry-trace": getMetaContent("sentry-trace"),
    },
    middleware: [
        new CSRFMiddleware(),
        new EventMiddleware(),
        new LoggingMiddleware(CurrentTenantFromJSON(globalAK()?.tenant)),
    ],
});

// This is just a function so eslint doesn't complain about
// missing-whitespace-between-attributes or
// unexpected-character-in-attribute-name
export function AndNext(url: string): string {
    return `?next=${encodeURIComponent(url)}`;
}

window.addEventListener(EVENT_REFRESH, () => {
    // Upon global refresh, disregard whatever was pre-hydrated and
    // actually load info from API
    globalConfigPromise = undefined;
    globalTenantPromise = undefined;
    config();
    tenant();
});

console.debug(`authentik(early): version ${VERSION()}, apiBase ${DEFAULT_CONFIG.basePath}`);
