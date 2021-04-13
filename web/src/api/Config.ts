import { Configuration, Middleware, ResponseContext } from "authentik-api";
import { getCookie } from "../utils";
import { API_DRAWER_MIDDLEWARE } from "../elements/notifications/APIDrawer";
import { MessageMiddleware } from "../elements/messages/Middleware";

export class LoggingMiddleware implements Middleware {

    post(context: ResponseContext): Promise<Response | void> {
        console.debug(`authentik/api: ${context.response.status} ${context.init.method} ${context.url}`);
        return Promise.resolve(context.response);
    }

}

export const DEFAULT_CONFIG = new Configuration({
    basePath: "/api/v2beta",
    headers: {
        "X-CSRFToken": getCookie("authentik_csrf"),
        "X-Authentik-Prevent-Basic": "true"
    },
    middleware: [
        API_DRAWER_MIDDLEWARE,
        new MessageMiddleware(),
        new LoggingMiddleware(),
    ],
});
