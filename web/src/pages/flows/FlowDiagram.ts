import FlowChart from "flowchart.js";

import { LitElement, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { FlowsApi } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../api/Config";
import { EVENT_REFRESH } from "../../constants";
import "../../elements/EmptyState";

export const FONT_COLOUR_DARK_MODE = "#fafafa";
export const FONT_COLOUR_LIGHT_MODE = "#151515";
export const FILL_DARK_MODE = "#18191a";
export const FILL_LIGHT_MODE = "#f0f0f0";

@customElement("ak-flow-diagram")
export class FlowDiagram extends LitElement {
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

    @property()
    fontColour: string = FONT_COLOUR_DARK_MODE;

    @property()
    fill: string = FILL_DARK_MODE;

    handlerBound = false;

    createRenderRoot(): Element | ShadowRoot {
        return this;
    }

    get isInViewport(): boolean {
        const rect = this.getBoundingClientRect();
        return !(rect.x + rect.y + rect.width + rect.height === 0);
    }

    constructor() {
        super();
        const matcher = window.matchMedia("(prefers-color-scheme: light)");
        const handler = (ev?: MediaQueryListEvent) => {
            if (ev?.matches || matcher.matches) {
                this.fontColour = FONT_COLOUR_LIGHT_MODE;
                this.fill = FILL_LIGHT_MODE;
            } else {
                this.fontColour = FONT_COLOUR_DARK_MODE;
                this.fill = FILL_DARK_MODE;
            }
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
        if (this.diagram) {
            const diagram = FlowChart.parse(this.diagram);
            diagram.drawSVG(this, {
                "font-color": this.fontColour,
                "line-color": "#bebebe",
                "element-color": "#bebebe",
                "fill": this.fill,
                "yes-text": "Policy passes",
                "no-text": "Policy denies",
            });
            return html``;
        }
        return html`<ak-empty-state ?loading=${true}></ak-empty-state>`;
    }
}
