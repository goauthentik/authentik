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
        globalTenantPromise = new CoreApi(DEFAULT_CONFIG).coreTenantsCurrentRetrieve();
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
