import "#elements/router/Router404";
import "#elements/a11y/ak-skip-to-content";

import { ROUTE_SEPARATOR } from "#common/constants";

import { type AKSkipToContent, findMainContent } from "#elements/a11y/ak-skip-to-content";
import { AKElement } from "#elements/Base";
import { RouteChangeEvent } from "#elements/router/events";
import { Route } from "#elements/router/Route";
import { RouteMatch } from "#elements/router/RouteMatch";
import { ifPreviousValue, onlyBinding } from "#elements/utils/properties";

import { ConsoleLogger } from "#logger/browser";

import {
    getClient,
    SEMANTIC_ATTRIBUTE_SENTRY_SOURCE,
    Span,
    startBrowserTracingNavigationSpan,
    startBrowserTracingPageLoadSpan,
} from "@sentry/browser";
import { BaseTransportOptions, Client, ClientOptions } from "@sentry/core";

import { html, PropertyValues, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

// Poliyfill for hashchange.newURL,
// https://developer.mozilla.org/en-US/docs/Web/API/WindowEventHandlers/onhashchange
window.addEventListener("load", () => {
    if (window.HashChangeEvent) {
        return;
    }

    let lastURL = document.URL;

    window.addEventListener("hashchange", (event) => {
        Object.defineProperty(event, "oldURL", {
            enumerable: true,
            configurable: true,
            value: lastURL,
        });

        Object.defineProperty(event, "newURL", {
            enumerable: true,
            configurable: true,
            value: document.URL,
        });
        lastURL = document.URL;
    });
});

export function paramURL(url: string, params?: { [key: string]: unknown }): string {
    let finalUrl = "#";
    finalUrl += url;
    if (params) {
        finalUrl += ";";
        finalUrl += encodeURIComponent(JSON.stringify(params));
    }
    return finalUrl;
}
export function navigate(url: string, params?: { [key: string]: unknown }): void {
    window.location.assign(paramURL(url, params));
}

@customElement("ak-router-outlet")
export class RouterOutlet extends AKElement {
    #logger = ConsoleLogger.prefix("router");
    protected createRenderRoot() {
        return this;
    }

    //#region Properties

    public override role = "presentation";

    @property({
        attribute: false,
        useDefault: true,
        hasChanged: ifPreviousValue,
    })
    public current: RouteMatch | null = null;

    @property({
        type: String,
        attribute: "default-url",
        useDefault: true,
        hasChanged: ifPreviousValue,
    })
    public defaultURL: string | null = null;

    @property(onlyBinding)
    public routes: Route[] = [];

    //#endregion

    //#region Lifecycle

    #sentryClient: Client<ClientOptions<BaseTransportOptions>> | null = getClient() || null;
    #pageLoadSpan: Span | null = null;

    constructor() {
        super();

        window.addEventListener("hashchange", this.navigate);

        if (process.env.NODE_ENV !== "production" && this.#sentryClient) {
            this.#pageLoadSpan =
                startBrowserTracingPageLoadSpan(this.#sentryClient, {
                    name: window.location.pathname,
                    attributes: {
                        [SEMANTIC_ATTRIBUTE_SENTRY_SOURCE]: "url",
                    },
                }) || null;
        }
    }

    //#endregion

    public override connectedCallback(): void {
        super.connectedCallback();

        this.navigate();

        this.#mutationObserver.observe(this.renderRoot, {
            childList: true,
        });
    }

    //#endregion

    //#region a11y

    #skipToContentElement = document.querySelector<AKSkipToContent>("ak-skip-to-content");

    #synchronizeContentTarget = () => {
        if (!this.#skipToContentElement) return;

        const element = findMainContent(this);

        if (element) {
            this.#skipToContentElement.targetElement = element;
        }
    };

    #mutationObserver = new MutationObserver(this.#synchronizeContentTarget);

    //#endregion

    protected navigate = (event?: HashChangeEvent): void => {
        let activeUrl = window.location.hash.slice(1).split(ROUTE_SEPARATOR)[0];

        if (event) {
            // Check if we've actually changed paths
            const oldPath = new URL(event.oldURL).hash.slice(1).split(ROUTE_SEPARATOR)[0];

            if (oldPath === activeUrl) return;
        }
        if (activeUrl === "") {
            activeUrl = this.defaultURL || "/";
            window.location.hash = `#${activeUrl}`;

            this.#logger.info(`Defaulted URL to ${window.location.hash}`);

            return;
        }

        let matchedRoute: RouteMatch | null = null;

        for (const route of this.routes) {
            const match = route.url.exec(activeUrl);

            if (match !== null) {
                matchedRoute = new RouteMatch(route, activeUrl);
                matchedRoute.arguments = match.groups || {};

                this.#logger.debug(matchedRoute);

                break;
            }
        }

        if (!matchedRoute) {
            this.#logger.info(`Route "${activeUrl}" not defined`);
            const route = new Route(RegExp(""), async () => {
                return html`<div class="pf-c-page__main">
                    <ak-router-404 url=${activeUrl}></ak-router-404>
                </div>`;
            });
            matchedRoute = new RouteMatch(route, activeUrl);
            matchedRoute.arguments = route.url.exec(activeUrl)?.groups || {};
        }
        this.current = matchedRoute;

        this.dispatchEvent(new RouteChangeEvent(matchedRoute));
    };

    protected override updated(changedProperties: PropertyValues<this>): void {
        if (!changedProperties.has("current") || !this.current) return;
        if (!this.#sentryClient) return;

        // https://docs.sentry.io/platforms/javascript/tracing/instrumentation/automatic-instrumentation/#custom-routing
        if (this.#pageLoadSpan) {
            this.#pageLoadSpan.updateName(this.current.sanitizedURL());
            this.#pageLoadSpan.setAttribute(SEMANTIC_ATTRIBUTE_SENTRY_SOURCE, "route");
            this.#pageLoadSpan = null;
        } else {
            startBrowserTracingNavigationSpan(this.#sentryClient, {
                op: "navigation",
                name: this.current.sanitizedURL(),
                attributes: {
                    [SEMANTIC_ATTRIBUTE_SENTRY_SOURCE]: "route",
                },
            });
        }
    }

    render(): TemplateResult | undefined {
        return this.current?.render();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-router-outlet": RouterOutlet;
    }
}
