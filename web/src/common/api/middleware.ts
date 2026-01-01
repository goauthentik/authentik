import { EVENT_REQUEST_POST } from "#common/constants";
import { autoDetectLanguage } from "#common/ui/locale/utils";
import { getCookie } from "#common/utils";

import {
    CurrentBrand,
    FetchParams,
    Middleware,
    RequestContext,
    ResponseContext,
} from "@goauthentik/api";

import { LOCALE_STATUS_EVENT, LocaleStatusEventDetail } from "@lit/localize";

export const CSRFHeaderName = "X-authentik-CSRF";
export const AcceptLanguage = "Accept-Language";

export interface RequestInfo {
    time: number;
    method: string;
    path: string;
    status: number;
}

export class LoggingMiddleware implements Middleware {
    #logPrefix: string;

    constructor(brand: CurrentBrand) {
        this.#logPrefix = `%c[api/${brand.matchedDomain}]: `;
    }

    post(context: ResponseContext): Promise<Response | void> {
        let msg = this.#logPrefix;

        // https://developer.mozilla.org/en-US/docs/Web/API/console#styling_console_output
        msg += `%c${context.response.status}%c ${context.init.method} ${context.url}`;

        const style = context.response.ok
            ? "color: green; font-weight: bold;"
            : "color: red; font-weight: bold;";

        console.debug(msg, "font-weight: bold;", style, "");
        return Promise.resolve(context.response);
    }
}

export class CSRFMiddleware implements Middleware {
    pre?(context: RequestContext): Promise<FetchParams | void> {
        context.init.headers = {
            ...context.init.headers,
            [CSRFHeaderName]: getCookie("authentik_csrf"),
        };

        return Promise.resolve(context);
    }
}

export class EventMiddleware implements Middleware {
    post?(context: ResponseContext): Promise<Response | void> {
        const request: RequestInfo = {
            time: new Date().getTime(),
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

export class LocaleMiddleware implements Middleware, Disposable {
    #locale: string;

    #localeStatusListener = (event: CustomEvent<LocaleStatusEventDetail>) => {
        if (event.detail.status !== "ready") {
            return;
        }

        this.#locale = event.detail.readyLocale;
    };

    constructor(localeHint?: string) {
        this.#locale = autoDetectLanguage(localeHint);

        window.addEventListener(LOCALE_STATUS_EVENT, this.#localeStatusListener);
    }

    [Symbol.dispose]() {
        window.removeEventListener(LOCALE_STATUS_EVENT, this.#localeStatusListener);
    }

    pre(context: RequestContext): Promise<FetchParams | void> {
        context.init.headers = {
            ...context.init.headers,
            [AcceptLanguage]: this.#locale,
        };

        return Promise.resolve(context);
    }
}
