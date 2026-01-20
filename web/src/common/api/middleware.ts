import { AKRequestPostEvent, APIRequestInfo } from "#common/api/events";
import { formatAcceptLanguageHeader } from "#common/ui/locale/utils";
import { getCookie } from "#common/utils";

import { ConsoleLogger, Logger } from "#logger/browser";

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

export class LoggingMiddleware implements Middleware {
    #logger: Logger;

    constructor(brand: CurrentBrand) {
        const prefix =
            brand.matchedDomain === "authentik-default" ? "api" : `api/${brand.matchedDomain}`;

        this.#logger = ConsoleLogger.prefix(prefix);
    }

    post({ response, init, url }: ResponseContext): Promise<Response> {
        const parsedURL = URL.canParse(url) ? new URL(url) : null;
        const path = parsedURL ? parsedURL.pathname + parsedURL.search : url;
        if (response.ok) {
            this.#logger.debug(`${init.method} ${path}`);
        } else {
            this.#logger.warn(`${response.status} ${init.method} ${path}`);
        }

        return Promise.resolve(response);
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
        const requestInfo: APIRequestInfo = {
            time: new Date().getTime(),
            method: (context.init.method || "GET").toUpperCase(),
            path: context.url,
            status: context.response.status,
        };

        window.dispatchEvent(new AKRequestPostEvent(requestInfo));

        return Promise.resolve(context.response);
    }
}

export class LocaleMiddleware implements Middleware, Disposable {
    #locale: string;

    #localeStatusListener = (event: CustomEvent<LocaleStatusEventDetail>) => {
        if (event.detail.status !== "ready") {
            return;
        }

        this.#locale = formatAcceptLanguageHeader(event.detail.readyLocale);
    };

    constructor(languageTagHint: Intl.UnicodeBCP47LocaleIdentifier) {
        this.#locale = formatAcceptLanguageHeader(languageTagHint);

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
