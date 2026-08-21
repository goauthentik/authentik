/**
 * @file Path-router outlet for the new route table.
 *
 * Renders the route matched from `location.pathname` (with the interface
 * `prefix` stripped per the matcher's leading-slash contract), owns the
 * loading and error states, and claims in-interface anchor clicks. Ships
 * inert: nothing imports it until the interface flip in Plan 3b.
 *
 * App-context-free: imports only the router core, the reused 404/empty-state
 * elements, `AKElement`, lit, `@sentry/browser`, and `@lit/localize`.
 */

import "#elements/router/Router404";
import "#elements/EmptyState";

import { AKElement } from "#elements/Base";
import { getRouterConfig } from "#elements/router/core/config";
import { applyHashRedirect } from "#elements/router/core/hash-shim";
import { matchRoute, type RouteMatch } from "#elements/router/core/matcher";
import {
    createClickInterceptor,
    navigate,
    RouterNavigateEvent,
} from "#elements/router/core/navigation";
import { Route } from "#elements/router/core/Route";
import { type SlottedTemplateResult } from "#elements/types";

import {
    getClient,
    SEMANTIC_ATTRIBUTE_SENTRY_SOURCE,
    type Span,
    startBrowserTracingNavigationSpan,
    startBrowserTracingPageLoadSpan,
} from "@sentry/browser";

import { msg } from "@lit/localize";
import { html, type PropertyValues, type TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

/**
 * Build a Sentry span name by joining the interface `prefix` to the matched
 * route `name` with exactly one slash — a bare name (`"library"`) and a
 * default-route name that carries its own leading slash (`"/x"`) both yield a
 * single separator. A `null` name (the 404 / unmatched branch) passes the raw
 * `pathname` through unchanged.
 */
export function formatSpanName(prefix: string, routeName: string | null, pathname: string): string {
    if (routeName === null) return pathname;

    return `${prefix.replace(/\/+$/, "")}/${routeName.replace(/^\/+/, "")}`;
}

@customElement("ak-router-view")
export class RouterView extends AKElement {
    /**
     * Render into the light DOM so PatternFly page styles cascade and the 404 /
     * empty-state children resolve normally. Mirrors the legacy outlet.
     */
    protected override createRenderRoot() {
        return this;
    }

    public override role = "presentation";

    //#region Properties

    @property({ attribute: false })
    public routes: Route[] = [];

    @property({ type: String })
    public prefix = "";

    @property({ type: String, attribute: "default-path" })
    public defaultPath = "/";

    @state()
    private current: RouteMatch<Route> | null = null;

    //#endregion

    //#region Sentry

    #sentryClient = getClient();
    #pageLoadSpan: Span | null = null;

    constructor() {
        super();

        if (process.env.NODE_ENV !== "production" && this.#sentryClient) {
            this.#pageLoadSpan =
                startBrowserTracingPageLoadSpan(this.#sentryClient, {
                    name: window.location.pathname,
                    attributes: {
                        [SEMANTIC_ATTRIBUTE_SENTRY_SOURCE]: "url",
                    },
                }) ?? null;
        }
    }

    //#endregion

    //#region Lifecycle

    #clickHandler = createClickInterceptor(
        () => {
            const { base, interfaceName } = getRouterConfig();

            return {
                origin: window.location.origin,
                base,
                interfaceName,
                currentPathname: window.location.pathname,
                currentSearch: window.location.search,
            };
        },
        (url) => navigate(url),
    );

    #onPopState = (): void => this.#syncRoute();
    #onNavigate = (): void => this.#syncRoute();

    public override connectedCallback(): void {
        super.connectedCallback();

        window.addEventListener("popstate", this.#onPopState);
        window.addEventListener(RouterNavigateEvent.eventName, this.#onNavigate);
        document.addEventListener("click", this.#clickHandler, { capture: true });

        applyHashRedirect();
        this.#syncRoute();
    }

    public override disconnectedCallback(): void {
        window.removeEventListener("popstate", this.#onPopState);
        window.removeEventListener(RouterNavigateEvent.eventName, this.#onNavigate);
        document.removeEventListener("click", this.#clickHandler, { capture: true });

        super.disconnectedCallback();
    }

    //#endregion

    //#region Matching

    /**
     * Strip the interface prefix, preserving the leading slash the matcher
     * requires: `/if/user/settings` → `/settings`, `/if/user/` → `/`. A
     * pathname outside the prefix is returned unchanged so it falls through to
     * the 404 branch.
     */
    #strip(pathname: string): string {
        if (!pathname.startsWith(this.prefix)) return pathname;

        return `/${pathname.slice(this.prefix.length).replace(/^\/+/, "")}`;
    }

    /**
     * Join a route-relative path onto the prefix for navigation.
     */
    #join(path: string): string {
        return `${this.prefix}${path.replace(/^\/+/, "")}`;
    }

    #syncRoute = (): void => {
        let stripped = this.#strip(window.location.pathname);

        if (stripped === "/" && this.defaultPath !== "/") {
            // `navigate` applies `replaceState` synchronously, so re-reading the
            // location yields the redirected path immediately.
            navigate(this.#join(this.defaultPath), { mode: "replace" });
            stripped = this.#strip(window.location.pathname);
        }

        this.current = matchRoute(stripped, this.routes);
    };

    //#endregion

    //#region Rendering

    async #resolve(match: RouteMatch<Route>): Promise<SlottedTemplateResult> {
        try {
            return await match.route.resolve(match.parameters);
        } catch (error) {
            return this.#renderError(error);
        }
    }

    #renderError(error: unknown): SlottedTemplateResult {
        const message = error instanceof Error ? error.message : String(error);

        return html`<ak-empty-state icon="fa-times-circle">
            <span>${msg("This page failed to load.", { id: "router.view.error.heading" })}</span>
            <span slot="body">${message}</span>
        </ak-empty-state>`;
    }

    #spanName(): string {
        return formatSpanName(
            this.prefix,
            this.current?.route.name ?? null,
            window.location.pathname,
        );
    }

    protected override updated(changedProperties: PropertyValues): void {
        if (!changedProperties.has("current")) return;
        if (!this.#sentryClient) return;

        const name = this.#spanName();

        if (this.#pageLoadSpan) {
            this.#pageLoadSpan.updateName(name);
            this.#pageLoadSpan.setAttribute(SEMANTIC_ATTRIBUTE_SENTRY_SOURCE, "route");
            this.#pageLoadSpan = null;
        } else {
            startBrowserTracingNavigationSpan(this.#sentryClient, {
                op: "navigation",
                name,
                attributes: {
                    [SEMANTIC_ATTRIBUTE_SENTRY_SOURCE]: "route",
                },
            });
        }
    }

    render(): TemplateResult {
        if (!this.current) {
            return html`<ak-router-404 url=${window.location.pathname}></ak-router-404>`;
        }

        return html`${until(
            this.#resolve(this.current),
            html`<ak-empty-state loading></ak-empty-state>`,
        )}`;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-router-view": RouterView;
    }
}
