import { globalAK } from "@goauthentik/web/api/Global";
import { EVENT_REFRESH, VERSION } from "@goauthentik/web/constants";
import { MessageMiddleware } from "@goauthentik/web/elements/messages/Middleware";
import { APIMiddleware } from "@goauthentik/web/elements/notifications/APIDrawer";
import { activateLocale } from "@goauthentik/web/interfaces/locale";
import { getCookie } from "@goauthentik/web/utils";

import {
    Config,
    ConfigFromJSON,
    Configuration,
    CoreApi,
    CurrentTenant,
    CurrentTenantFromJSON,
    FetchParams,
    Middleware,
    RequestContext,
    ResponseContext,
    RootApi,
} from "@goauthentik/api";

export class LoggingMiddleware implements Middleware {
    post(context: ResponseContext): Promise<Response | void> {
        tenant().then((tenant) => {
            let msg = `authentik/api[${tenant.matchedDomain}]: `;
            msg += `${context.response.status} ${context.init.method} ${context.url}`;
            console.debug(msg);
        });
        return Promise.resolve(context.response);
    }
}

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

export class CSRFMiddleware implements Middleware {
    pre?(context: RequestContext): Promise<FetchParams | void> {
        // @ts-ignore
        context.init.headers["X-authentik-CSRF"] = getCookie("authentik_csrf");
        return Promise.resolve(context);
    }
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
        new APIMiddleware(),
        new MessageMiddleware(),
        new LoggingMiddleware(),
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

console.debug(`authentik(early): version ${VERSION}, apiBase ${DEFAULT_CONFIG.basePath}`);
