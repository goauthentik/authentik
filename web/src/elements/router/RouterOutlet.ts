import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { Route } from "./Route";
import { ROUTES } from "../../routes";
import { RouteMatch } from "./RouteMatch";

import "../../pages/generic/SiteShell";
import "./Router404";

@customElement("ak-router-outlet")
export class RouterOutlet extends LitElement {
    @property({attribute: false})
    current?: RouteMatch;

    @property()
    defaultUrl?: string;

    static get styles(): CSSResult[] {
        return [
            css`
                :host {
                    height: 100vh;
                }
                *:first-child {
                    height: 100%;
                    display: flex;
                    flex-direction: column;
                }
            `,
        ];
    }

    constructor() {
        super();
        window.addEventListener("hashchange", () => this.navigate());
    }

    firstUpdated(): void {
        this.navigate();
    }

    navigate(): void {
        let activeUrl = window.location.hash.slice(1, Infinity);
        if (activeUrl === "") {
            activeUrl = this.defaultUrl || "/";
            window.location.hash = `#${activeUrl}`;
            console.debug(`authentik/router: defaulted URL to ${window.location.hash}`);
            return;
        }
        let matchedRoute: RouteMatch | null = null;
        ROUTES.some((route) => {
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
                </div>`
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
