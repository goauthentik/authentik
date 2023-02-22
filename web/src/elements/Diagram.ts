import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/EmptyState";
import mermaid from "mermaid";

import { CSSResult, TemplateResult, css, html } from "lit";
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

    constructor() {
        super();
        const matcher = window.matchMedia("(prefers-color-scheme: light)");
        const handler = (ev?: MediaQueryListEvent) => {
            mermaid.initialize({
                // The type definition for this says number
                // but the example use strings
                // and numbers don't work
                logLevel: "fatal" as unknown as number,
                startOnLoad: false,
                theme: ev?.matches || matcher.matches ? "default" : "dark",
                flowchart: {
                    curve: "linear",
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
