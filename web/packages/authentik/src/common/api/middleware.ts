import { EVENT_REQUEST_POST } from "@goauthentik/common/constants";
import { getCookie } from "@goauthentik/common/utils";

import {
    CurrentTenant,
    FetchParams,
    Middleware,
    RequestContext,
    ResponseContext,
} from "@goauthentik/api";

export const CSRFHeaderName = "X-authentik-CSRF";

export interface RequestInfo {
    method: string;
    path: string;
    status: number;
}

export class LoggingMiddleware implements Middleware {
    tenant: CurrentTenant;
    constructor(tenant: CurrentTenant) {
        this.tenant = tenant;
    }

    post(context: ResponseContext): Promise<Response | void> {
        let msg = `authentik/api[${this.tenant.matchedDomain}]: `;
        // https://developer.mozilla.org/en-US/docs/Web/API/console#styling_console_output
        msg += `%c${context.response.status}%c ${context.init.method} ${context.url}`;
        let style = "";
        if (context.response.status >= 400) {
            style = "color: red; font-weight: bold;";
        }
        console.debug(msg, style, "");
        return Promise.resolve(context.response);
    }
}

export class CSRFMiddleware implements Middleware {
    pre?(context: RequestContext): Promise<FetchParams | void> {
        // @ts-ignore
        context.init.headers[CSRFHeaderName] = getCookie("authentik_csrf");
        return Promise.resolve(context);
    }
}

export class EventMiddleware implements Middleware {
    post?(context: ResponseContext): Promise<Response | void> {
        const request: RequestInfo = {
            method: (context.init.method || "GET").toUpperCase(),
            path: context.url,
            status: context.response.status,
        };
        window.dispatchEvent(
            new CustomEvent(EVENT_REQUEST_POST, {
                bubbles: true,
                composed: true,
                detail: request,
            }),
        );
        return Promise.resolve(context.response);
    }
}
