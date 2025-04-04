import { AKElement } from "@goauthentik/elements/Base";
import { Route } from "@goauthentik/elements/router/Route";
import "@goauthentik/elements/router/Router404";
import { matchRoute, pluckRoute } from "@goauthentik/elements/router/utils";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

// Poliyfill for hashchange.newURL,
// https://developer.mozilla.org/en-US/docs/Web/API/WindowEventHandlers/onhashchange
window.addEventListener("load", () => {
    if (window.HashChangeEvent) return;

    console.debug("authentik/router: polyfilling hashchange event");

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
});

@customElement("ak-router-outlet")
export class RouterOutlet extends AKElement {
    @state()
    private currentPathname: string | null = null;

    @property()
    public defaultURL?: string;

    @property({ attribute: false })
    public routes: Route[] = [];

    static get styles(): CSSResult[] {
        return [
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

    connectedCallback(): void {
        super.connectedCallback();

        window.addEventListener("hashchange", this.#refreshLocation);
    }

    disconnectedCallback(): void {
        super.disconnectedCallback();

        window.removeEventListener("hashchange", this.#refreshLocation);
    }

    protected firstUpdated(): void {
        const currentPathname = pluckRoute(window.location).pathname;

        if (currentPathname) return;

        console.debug("authentik/router: defaulted route to empty pathname");

        this.#redirectToDefault();
    }

    #redirectToDefault(): void {
        const nextPathname = this.defaultURL || "/";

        window.location.hash = "#" + nextPathname;
    }

    #refreshLocation = (event: HashChangeEvent): void => {
        console.debug("authentik/router: hashchange event", event);
        const nextPathname = pluckRoute(event.newURL).pathname;
        const previousPathname = pluckRoute(event.oldURL).pathname;

        if (previousPathname === nextPathname) {
            console.debug("authentik/router: hashchange event, but no change in path", event, {
                currentPathname: nextPathname,
                previousPathname,
            });

            return;
        }

        if (!nextPathname) {
            console.debug(`authentik/router: defaulted route to ${nextPathname}`);

            this.#redirectToDefault();
            return;
        }

        this.currentPathname = nextPathname;
    };

    render(): TemplateResult | undefined {
        let currentPathname = this.currentPathname;

        if (!currentPathname) {
            currentPathname = pluckRoute(window.location).pathname;
        }

        const match = matchRoute(currentPathname, this.routes);

        if (!match) {
            return html`<div class="pf-c-page__main">
                <ak-router-404 pathname=${currentPathname}></ak-router-404>
            </div>`;
        }

        console.debug("authentik/router: found match", match);

        const { parameters, route } = match;

        return route.render(parameters);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-router-outlet": RouterOutlet;
    }
}
