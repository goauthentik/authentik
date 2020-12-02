import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
// @ts-ignore
import CodeMirrorStyle from "codemirror/lib/codemirror.css";
// @ts-ignore
import CodeMirrorTheme from "codemirror/theme/monokai.css";
import { ColorStyles } from "../../constants";
import { COMMON_STYLES } from "../../common/styles";
import { Route } from "./Route";
import { ROUTES } from "../../routes";
import { RouteMatch } from "./RouteMatch";

import "../generic/SiteShell";

@customElement("pb-router-outlet")
export class RouterOutlet extends LitElement {
    @property({attribute: false})
    current?: RouteMatch;

    @property()
    defaultUrl?: string;

    static get styles(): CSSResult[] {
        return [
            CodeMirrorStyle,
            CodeMirrorTheme,
            ColorStyles,
            css`
                :host {
                    height: 100%;
                }
            `,
        ].concat(...COMMON_STYLES);
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
            console.debug(`passbook/router: set to ${window.location.hash}`);
            return;
        }
        let matchedRoute: RouteMatch | null = null;
        ROUTES.some((route) => {
            console.debug(`passbook/router: matching ${activeUrl} against ${route.url}`);
            const match = route.url.exec(activeUrl);
            if (match != null) {
                matchedRoute = new RouteMatch(route);
                matchedRoute.arguments = match.groups || {};
                matchedRoute.fullUrl = activeUrl;
                console.debug(`passbook/router: found match ${matchedRoute}`);
                return true;
            }
        });
        if (!matchedRoute) {
            console.debug(`passbook/router: route "${activeUrl}" not defined, defaulting to shell`);
            const route = new Route(
                RegExp(""),
                html`<pb-site-shell url=${activeUrl}>
                    <div slot="body"></div>
                </pb-site-shell>`
            );
            matchedRoute = new RouteMatch(route);
            matchedRoute.arguments = route.url.exec(activeUrl)?.groups || {};
            matchedRoute.fullUrl = activeUrl;
        }
        this.current = matchedRoute;
    }

    render(): TemplateResult | undefined {
        // TODO: Render 404 when current Route is empty
        return this.current?.render();
    }
}
