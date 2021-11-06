import { Config, Configuration, CoreApi, CurrentTenant, Middleware, ResponseContext, RootApi } from "@goauthentik/api";
import { getCookie } from "../utils";
import { APIMiddleware } from "../elements/notifications/APIDrawer";
import { MessageMiddleware } from "../elements/messages/Middleware";
import { VERSION } from "../constants";

export class LoggingMiddleware implements Middleware {

    post(context: ResponseContext): Promise<Response | void> {
        tenant().then(tenant => {
            let msg = `authentik/api[${tenant.matchedDomain}]: `;
            msg += `${context.response.status} ${context.init.method} ${context.url}`;
            console.debug(msg);
        });
        return Promise.resolve(context.response);
    }

}

let globalConfigPromise: Promise<Config>;
export function config(): Promise<Config> {
    if (!globalConfigPromise) {
        globalConfigPromise = new RootApi(DEFAULT_CONFIG).rootConfigRetrieve();
    }
    return globalConfigPromise;
}

let globalTenantPromise: Promise<CurrentTenant>;
export function tenant(): Promise<CurrentTenant> {
    if (!globalTenantPromise) {
        globalTenantPromise = new CoreApi(DEFAULT_CONFIG).coreTenantsCurrentRetrieve().then(tenant => {
            /**
             *  <link rel="icon" href="/static/dist/assets/icons/icon.png">
             *  <link rel="shortcut icon" href="/static/dist/assets/icons/icon.png">
             */
            const rels = ["icon", "shortcut icon"];
            rels.forEach(rel => {
                let relIcon = document.head.querySelector<HTMLLinkElement>(`link[rel='${rel}']`);
                if (!relIcon) {
                    relIcon = document.createElement('link');
                    relIcon.rel = rel;
                    document.getElementsByTagName('head')[0].appendChild(relIcon);
                }
                relIcon.href = tenant.brandingFavicon;
            })
            return tenant;
        });
    }
    return globalTenantPromise;
}

export const DEFAULT_CONFIG = new Configuration({
    basePath: process.env.AK_API_BASE_PATH + "/api/v3",
    headers: {
        "X-CSRFToken": getCookie("authentik_csrf"),
    },
    middleware: [
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

console.debug(`authentik(early): version ${VERSION}, apiBase ${DEFAULT_CONFIG.basePath}`);
