import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/EmptyState";
import mermaid from "mermaid";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

import { FlowsApi } from "@goauthentik/api";

export const FONT_COLOUR_DARK_MODE = "#fafafa";
export const FONT_COLOUR_LIGHT_MODE = "#151515";
export const FILL_DARK_MODE = "#18191a";
export const FILL_LIGHT_MODE = "#f0f0f0";

@customElement("ak-flow-diagram")
export class FlowDiagram extends AKElement {
    _flowSlug?: string;

    @property()
    set flowSlug(value: string) {
        this._flowSlug = value;
        this.diagram = undefined;
        new FlowsApi(DEFAULT_CONFIG)
            .flowsInstancesDiagramRetrieve({
                slug: value,
            })
            .then((data) => {
                this.diagram = data.diagram;
                this.requestUpdate();
            });
    }

    @property({ attribute: false })
    diagram?: string;

    handlerBound = false;

    get isInViewport(): boolean {
        const rect = this.getBoundingClientRect();
        return !(rect.x + rect.y + rect.width + rect.height === 0);
    }

    constructor() {
        super();
        const matcher = window.matchMedia("(prefers-color-scheme: light)");
        const handler = (ev?: MediaQueryListEvent) => {
            console.log("setting config");
            mermaid.initialize({
                logLevel: "error",
                startOnLoad: false,
                theme: ev?.matches || matcher.matches ? "default" : "dark",
                flowchart: {
                    curve: "basis",
                },
            });
            this.requestUpdate();
        };
        matcher.addEventListener("change", handler);
        handler();
    }

    firstUpdated(): void {
        if (this.handlerBound) return;
        window.addEventListener(EVENT_REFRESH, this.refreshHandler);
        this.handlerBound = true;
    }

    refreshHandler = (): void => {
        if (!this._flowSlug) return;
        this.flowSlug = this._flowSlug;
    };

    disconnectedCallback(): void {
        super.disconnectedCallback();
        window.removeEventListener(EVENT_REFRESH, this.refreshHandler);
    }

    render(): TemplateResult {
        this.querySelectorAll("*").forEach((el) => {
            try {
                el.remove();
            } catch {
                console.debug(`authentik/flow/diagram: failed to remove element ${el}`);
            }
        });
        if (!this.diagram) {
            return html`<ak-empty-state ?loading=${true}></ak-empty-state>`;
        }
        return html`${unsafeHTML(mermaid.render("graph", this.diagram))}`;
    }
}
