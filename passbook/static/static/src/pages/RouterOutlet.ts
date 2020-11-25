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
    private callback?: () => TemplateResult;

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

    render(): TemplateResult {
        if (this.callback) {
            return this.callback();
        }
        if (this.element) {
            return this.element;
        }
        throw new Error("Route does not have callback or element");
    }
}

export const ROUTES: Route[] = [
    // Prevent infinite Shell loops
    new Route(new RegExp("^/$")).redirect("/-/overview/"),
    new Route(new RegExp("^/applications/$"), html`<h1>test</h1>`),
];

@customElement("pb-router-outlet")
export class RouterOutlet extends LitElement {
    @property()
    activeRoute?: Route;

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
        let selectedRoute: Route | null = null;
        ROUTES.forEach((route) => {
            if (route.url.exec(activeUrl)) {
                selectedRoute = route;
                return;
            }
        });
        if (!selectedRoute) {
            console.log(
                `passbook/router: route "${activeUrl}" not defined, defaulting to shell`
            );
            selectedRoute = new Route(
                RegExp(""),
                html`<pb-site-shell url=${activeUrl}>
                    <div slot="body"></div>
                </pb-site-shell>`
            );
        }
        this.activeRoute = selectedRoute;
    }

    render() {
        return this.activeRoute?.render();
    }
}
