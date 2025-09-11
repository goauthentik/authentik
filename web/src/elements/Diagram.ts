import "#elements/EmptyState";

import { EVENT_REFRESH, EVENT_THEME_CHANGE } from "#common/constants";
import { DOM_PURIFY_STRICT } from "#common/purify";

import { AKElement } from "#elements/Base";

import { UiThemeEnum } from "@goauthentik/api";

import mermaid, { MermaidConfig } from "mermaid";

import { css, CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";
import { until } from "lit/directives/until.js";

@customElement("ak-diagram")
export class Diagram extends AKElement {
    @property({ attribute: false })
    diagram?: string;

    refreshHandler = (): void => {
        if (!this.textContent) return;
        this.diagram = this.textContent;
    };

    handlerBound = false;

    static styles: CSSResult[] = [
        css`
            :host {
                display: flex;
                justify-content: center;
            }
        `,
    ];

    config: MermaidConfig;

    constructor() {
        super();
        this.config = {
            // The type definition for this says number
            // but the example use strings
            // and numbers don't work
            logLevel: "fatal",
            startOnLoad: false,
            flowchart: {
                curve: "linear",
            },
            htmlLabels: false,
            securityLevel: "strict",
            dompurifyConfig: DOM_PURIFY_STRICT,
        };
        mermaid.initialize(this.config);
    }

    firstUpdated(): void {
        if (this.handlerBound) return;
        window.addEventListener(EVENT_REFRESH, this.refreshHandler);
        this.addEventListener(EVENT_THEME_CHANGE, ((ev: CustomEvent<UiThemeEnum>) => {
            if (ev.detail === UiThemeEnum.Dark) {
                this.config.theme = "dark";
            } else {
                this.config.theme = "default";
            }
            mermaid.initialize(this.config);
        }) as EventListener);
        this.handlerBound = true;
        this.refreshHandler();
    }

    disconnectedCallback(): void {
        super.disconnectedCallback();
        window.removeEventListener(EVENT_REFRESH, this.refreshHandler);
    }

    render(): TemplateResult {
        this.querySelectorAll("*").forEach((el) => {
            try {
                el.remove();
            } catch {
                console.debug(`authentik/diagram: failed to remove element ${el}`);
            }
        });
        if (!this.diagram) {
            return html`<ak-empty-state loading></ak-empty-state>`;
        }
        return html`${until(
            mermaid.render("graph", this.diagram).then((r) => {
                r.bindFunctions?.(this.shadowRoot as unknown as Element);
                return unsafeHTML(r.svg);
            }),
        )}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-diagram": Diagram;
    }
}
