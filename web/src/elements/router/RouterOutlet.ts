import { CSSResult, LitElement, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import AKGlobal from "../../authentik.css";

import { ROUTE_SEPARATOR } from "../../constants";
import { Route } from "./Route";
import { RouteMatch } from "./RouteMatch";
import "./Router404";

// Poliyfill for hashchange.newURL,
// https://developer.mozilla.org/en-US/docs/Web/API/WindowEventHandlers/onhashchange
window.addEventListener("load", () => {
    if (!window.HashChangeEvent)
        (function () {
            let lastURL = document.URL;
            window.addEventListener("hashchange", function (event) {
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
        })();
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
export class RouterOutlet extends LitElement {
    @property({ attribute: false })
    current?: RouteMatch;

    @property()
    defaultUrl?: string;

    @property({ attribute: false })
    routes: Route[] = [];

    static get styles(): CSSResult[] {
        return [
            AKGlobal,
            css`
                :host {
                    background-color: transparent !important;
                }
                *:first-child {
                    flex-direction: column;
                }
            `,
        ];
    }

    constructor() {
        super();
        window.addEventListener("hashchange", (ev: HashChangeEvent) => this.navigate(ev));
    }

    firstUpdated(): void {
        this.navigate();
    }

    navigate(ev?: HashChangeEvent): void {
        let activeUrl = window.location.hash.slice(1, Infinity).split(ROUTE_SEPARATOR)[0];
        if (ev) {
            // Check if we've actually changed paths
            const oldPath = new URL(ev.oldURL).hash.slice(1, Infinity).split(ROUTE_SEPARATOR)[0];
            if (oldPath === activeUrl) return;
        }
        if (activeUrl === "") {
            activeUrl = this.defaultUrl || "/";
            window.location.hash = `#${activeUrl}`;
            console.debug(`authentik/router: defaulted URL to ${window.location.hash}`);
            return;
        }
        let matchedRoute: RouteMatch | null = null;
        this.routes.some((route) => {
            const match = route.url.exec(activeUrl);
            if (match != null) {
                matchedRoute = new RouteMatch(route);
                matchedRoute.arguments = match.groups || {};
                matchedRoute.fullUrl = activeUrl;
                console.debug("authentik/router: found match ", matchedRoute);
                return true;
            }
        });
        if (!matchedRoute) {
            console.debug(`authentik/router: route "${activeUrl}" not defined`);
            const route = new Route(
                RegExp(""),
                html`<div class="pf-c-page__main">
                    <ak-router-404 url=${activeUrl}></ak-router-404>
                </div>`,
            );
            matchedRoute = new RouteMatch(route);
            matchedRoute.arguments = route.url.exec(activeUrl)?.groups || {};
            matchedRoute.fullUrl = activeUrl;
        }
        this.current = matchedRoute;
    }

    render(): TemplateResult | undefined {
        return this.current?.render();
    }
}
