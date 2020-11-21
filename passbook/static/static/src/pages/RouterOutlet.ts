import {
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

export interface Route {
    url: RegExp;
    element: TemplateResult;
}

export const ROUTES: Route[] = [
    {
        url: new RegExp("^overview$"),
        element: html`<pb-site-shell url="/overview/"
            ><div slot="body"></div
        ></pb-site-shell>`,
    },
    // {
    //     url: new RegExp("^applications$"),
    //     element: html`<h1>test2</h1>`,
    // },
];

@customElement("pb-router-outlet")
export class RouterOutlet extends LitElement {
    @property()
    activeRoute?: Route;

    static get styles() {
        return [PF, PFAddons];
    }

    constructor() {
        super();
        this.navigate();
        window.addEventListener("hashchange", (e) => this.navigate());
    }

    navigate() {
        const activeUrl = window.location.hash.slice(1, Infinity);
        ROUTES.forEach((route) => {
            let selectedRoute: Route | null = null;
            if (route.url.exec(activeUrl)) {
                selectedRoute = route;
            }
            if (!selectedRoute) {
                console.log(
                    `passbook/router: route "${activeUrl}" not defined, defaulting to shell`
                );
                selectedRoute = {
                    url: RegExp(""),
                    element: html`<pb-site-shell url=${activeUrl}
                        ><div slot="body"></div
                    ></pb-site-shell>`,
                };
            }
            this.activeRoute = selectedRoute;
        });
    }

    render() {
        return this.activeRoute?.element;
    }
}
