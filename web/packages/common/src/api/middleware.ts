import { EVENT_REQUEST_POST } from "@goauthentik/common/constants.js";
import { getCookie } from "@goauthentik/common/utils.js";

import {
    CurrentBrand,
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

const HTTP_BAD_REQUEST = 400;

export class LoggingMiddleware implements Middleware {
    brand: CurrentBrand;
    constructor(brand: CurrentBrand) {
        this.brand = brand;
    }

    post(context: ResponseContext): Promise<Response | void> {
        let msg = `authentik/api[${this.brand.matchedDomain}]: `;
        // https://developer.mozilla.org/en-US/docs/Web/API/console#styling_console_output
        msg += `%c${context.response.status}%c ${context.init.method} ${context.url}`;
        let style = "";
        if (context.response.status >= HTTP_BAD_REQUEST) {
            style = "color: red; font-weight: bold;";
        }
        console.debug(msg, style, "");
        return Promise.resolve(context.response);
    }
}

export class CSRFMiddleware implements Middleware {
    pre?(context: RequestContext): Promise<FetchParams | void> {
        // @ts-expect-error Headers collection type does not recognize 'X-' headers.
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
