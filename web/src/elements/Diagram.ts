import { EVENT_REFRESH, EVENT_THEME_CHANGE } from "@goauthentik/common/constants";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/EmptyState";
import mermaid, { MermaidConfig } from "mermaid";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";
import { until } from "lit/directives/until.js";

import { UiThemeEnum } from "@goauthentik/api";

@customElement("ak-diagram")
export class Diagram extends AKElement {
    @property({ attribute: false })
    diagram?: string;

    refreshHandler = (): void => {
        if (!this.textContent) return;
        this.diagram = this.textContent;
    };

    handlerBound = false;

    static get styles(): CSSResult[] {
        return [
            css`
                :host {
                    display: flex;
                    justify-content: center;
                }
            `,
        ];
    }

    config: MermaidConfig;

    constructor() {
        super();
        this.config = {
            // The type definition for this says number
            // but the example use strings
            // and numbers don't work
            logLevel: "fatal" as unknown as number,
            startOnLoad: false,
            flowchart: {
                curve: "linear",
            },
            htmlLabels: false,
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
            return html`<ak-empty-state ?loading=${true}></ak-empty-state>`;
        }
        return html`${until(
            mermaid.render("graph", this.diagram).then((r) => {
                r.bindFunctions?.(this.shadowRoot as unknown as Element);
                return unsafeHTML(r.svg);
            }),
        )}`;
    }
}
