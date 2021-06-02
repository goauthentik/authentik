import { Config, Configuration, CoreApi, CurrentTenant, Middleware, ResponseContext, RootApi, Tenant } from "authentik-api";
import { getCookie } from "../utils";
import { API_DRAWER_MIDDLEWARE } from "../elements/notifications/APIDrawer";
import { MessageMiddleware } from "../elements/messages/Middleware";

export class LoggingMiddleware implements Middleware {

    post(context: ResponseContext): Promise<Response | void> {
        tenant().then(tenant => {
            console.debug(`authentik/api[${tenant.matchedDomain}]: ${context.response.status} ${context.init.method} ${context.url}`);
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
                let relIcon = document.head.querySelector<HTMLLinkElement>("link[rel=icon]");
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
    basePath: "",
    headers: {
        "X-CSRFToken": getCookie("authentik_csrf"),
    },
    middleware: [
        API_DRAWER_MIDDLEWARE,
        new MessageMiddleware(),
        new LoggingMiddleware(),
    ],
});
