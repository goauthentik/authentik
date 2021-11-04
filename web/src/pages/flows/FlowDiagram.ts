import FlowChart from "flowchart.js";

import { LitElement, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { FlowsApi } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../api/Config";
import { EVENT_REFRESH } from "../../constants";
import { loading } from "../../utils";

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
        new FlowsApi(DEFAULT_CONFIG)
            .flowsInstancesDiagramRetrieve({
                slug: value,
            })
            .then((data) => {
                this.diagram = FlowChart.parse(data.diagram || "");
            });
    }

    @property({ attribute: false })
    diagram?: FlowChart.Instance;

    @property()
    fontColour: string = FONT_COLOUR_DARK_MODE;

    @property()
    fill: string = FILL_DARK_MODE;

    createRenderRoot(): Element | ShadowRoot {
        return this;
    }

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this._flowSlug) return;
            this.flowSlug = this._flowSlug;
        });
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

    render(): TemplateResult {
        if (this.diagram) {
            this.diagram.drawSVG(this, {
                "font-color": this.fontColour,
                "line-color": "#bebebe",
                "element-color": "#bebebe",
                "fill": this.fill,
                "yes-text": "Policy passes",
                "no-text": "Policy denies",
            });
            return html``;
        }
        return loading(this.diagram, html``);
    }
}
