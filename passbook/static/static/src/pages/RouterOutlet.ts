import {
    css,
    customElement,
    html,
    LitElement,
    property,
    TemplateResult,
} from "lit-element";
// @ts-ignore
import PF from "@patternfly/patternfly/patternfly.css";
// @ts-ignore
import PFAddons from "@patternfly/patternfly/patternfly-addons.css";
// @ts-ignore
import FA from "@fortawesome/fontawesome-free/css/fontawesome.css";
// @ts-ignore
import PBGlobal from "../passbook.css";
// @ts-ignore
import CodeMirrorStyle from "codemirror/lib/codemirror.css";
// @ts-ignore
import CodeMirrorTheme from "codemirror/theme/monokai.css";
import { ColorStyles } from "../constants";

export class Route {
    url: RegExp;

    private element?: TemplateResult;
    private callback?: (args: { [key: string]: string; }) => TemplateResult;

    constructor(url: RegExp, element?: TemplateResult) {
        this.url = url;
        this.element = element;
    }

    redirect(to: string): Route {
        this.callback = () => {
            console.log(`passbook/router: redirecting ${to}`);
            window.location.hash = `#${to}`;
            return html``;
        };
        return this;
    }

    then(render: (args: { [key: string]: string; }) => TemplateResult): Route {
        this.callback = render;
        return this;
    }

    render(args: { [key: string]: string; }): TemplateResult {
        if (this.callback) {
            return this.callback(args);
        }
        if (this.element) {
            return this.element;
        }
        throw new Error("Route does not have callback or element");
    }
}

export const SLUG_REGEX = "[-a-zA-Z0-9_]+";
export const ROUTES: Route[] = [
    // Prevent infinite Shell loops
    new Route(new RegExp(`^/$`)).redirect("/-/overview/"),
    new Route(new RegExp(`^/applications/$`), html`<h1>test</h1>`),
    new Route(new RegExp(`^/-/applications/(?<slug>${SLUG_REGEX})/$`)).then((args) => {
        return html`<h1>test</h1>

        <span>${args.slug}</span>`;
    }),
];

class RouteMatch {
    route: Route;
    arguments?: RegExpExecArray;
    fullUrl?: string;

    constructor(route: Route) {
        this.route = route;
    }

    render(): TemplateResult {
        return this.route.render(this.arguments!.groups || {});
    }
}

@customElement("pb-router-outlet")
export class RouterOutlet extends LitElement {
    @property()
    current?: RouteMatch;

    @property()
    defaultUrl?: string;

    static get styles() {
        return [
            PF,
            PFAddons,
            FA,
            PBGlobal,
            CodeMirrorStyle,
            CodeMirrorTheme,
            ColorStyles,
            css`
                :host {
                    height: 100%;
                }
            `,
        ];
    }

    constructor() {
        super();
        window.addEventListener("hashchange", (e) => this.navigate());
    }

    firstUpdated() {
        this.navigate();
    }

    navigate() {
        let activeUrl = window.location.hash.slice(1, Infinity);
        if (activeUrl === "") {
            activeUrl = this.defaultUrl!;
            window.location.hash = `#${activeUrl}`;
            return;
        }
        let matchedRoute: RouteMatch | null = null;
        ROUTES.forEach((route) => {
            console.log(`matching ${activeUrl} against ${route.url}`);
            const match = route.url.exec(activeUrl);
            if (match != null) {
                matchedRoute = new RouteMatch(route);
                matchedRoute.arguments = match;
                matchedRoute.fullUrl = activeUrl;
                return;
            }
        });
        if (!matchedRoute) {
            console.log(
                `passbook/router: route "${activeUrl}" not defined, defaulting to shell`
            );
            const route = new Route(
                RegExp(""),
                html`<pb-site-shell url=${activeUrl}>
                    <div slot="body"></div>
                </pb-site-shell>`
            );
            matchedRoute = new RouteMatch(route);
            matchedRoute.arguments = route.url.exec(activeUrl)!;
            matchedRoute.fullUrl = activeUrl;
        }
        this.current = matchedRoute;
    }

    render() {
        return this.current?.render();
    }
}
