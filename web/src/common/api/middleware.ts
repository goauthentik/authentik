import { AKRequestPostEvent, APIRequestInfo } from "#common/api/events";
import { AKEnterpriseRefreshEvent, AKRefreshEvent } from "#common/events";
import { MessageLevel } from "#common/messages";
import { formatAcceptLanguageHeader } from "#common/ui/locale/utils";
import { getCookie } from "#common/utils";

import { showMessage } from "#elements/messages/MessageContainer";

import { ConsoleLogger, Logger } from "#logger/browser";

import {
    CurrentBrand,
    FetchParams,
    Middleware,
    RequestContext,
    ResponseContext,
} from "@goauthentik/api";

import { LOCALE_STATUS_EVENT, LocaleStatusEventDetail } from "@lit/localize";
import { html } from "lit";

export const CSRFHeaderName = "X-authentik-CSRF";
export const AcceptLanguage = "Accept-Language";

export class LoggingMiddleware implements Middleware {
    #logger: Logger;

    constructor(brand: CurrentBrand) {
        const prefix =
            brand.matchedDomain && brand.matchedDomain !== "authentik-default"
                ? `api/${brand.matchedDomain}`
                : "api";
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
export class DevRepeatedRequestsMiddleware implements Middleware, Disposable {
    #requests: string[] = [];
    #counts = new Map<string, number>();
    #warnings = new Set<string>();
    #logger = ConsoleLogger.prefix("repeated-requests-middleware");

    clear = () => {
        this.#logger.debug("Clearing count");
        this.#requests = [];
        this.#counts.clear();
        this.#warnings.clear();
    };

    constructor(protected readonly maxRequests: number = 10) {
        window.addEventListener("hashchange", this.clear);
        window.addEventListener(AKRefreshEvent.eventName, this.clear);
        window.addEventListener(AKEnterpriseRefreshEvent.eventName, this.clear);
    }

    public [Symbol.dispose]() {
        window.removeEventListener("hashchange", this.clear);
    }

    public async pre(context: RequestContext): Promise<FetchParams | void> {
        if (context.init.method?.toUpperCase() !== "GET" || !context.url) {
            return context;
        }

        const reqSig = context.url;
        const count = (this.#counts.get(reqSig) ?? 0) + 1;

        this.#counts.set(reqSig, count);
        this.#requests.push(reqSig);

        if (count > 2 && !this.#warnings.has(reqSig)) {
            this.#warnings.add(reqSig);

            const formattedURL = URL.canParse(reqSig) ? new URL(reqSig).pathname : reqSig;

            showMessage(
                {
                    level: MessageLevel.warning,
                    message: "[Dev] Consecutive requests detected",
                    description: html`${count} identical requests to
                        <pre style="text-wrap: auto">${formattedURL}</pre>`,
                },
                true,
            );

            this.#logger.trace("Repeated request", reqSig);
        }

        if (this.#requests.length > this.maxRequests) {
            const removed = this.#requests.shift()!;
            const removedCount = this.#counts.get(removed)!;

            if (removedCount === 1) {
                this.#counts.delete(removed);
                this.#warnings.delete(removed);
            } else {
                this.#counts.set(removed, removedCount - 1);
            }
        }

        return context;
    }
}
