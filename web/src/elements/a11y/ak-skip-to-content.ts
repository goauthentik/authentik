import { AKElement } from "#elements/Base";

import { msg } from "@lit/localize";
import { css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-skip-to-content")
export class AKSkipToContent extends AKElement {
    static styles = [
        PFBase,
        css`
            .show-on-focus:not(:focus) {
                width: 1px !important;
                height: 1px !important;
                padding: 0 !important;
                overflow: hidden !important;
                clip: rect(1px, 1px, 1px, 1px) !important;
                border: 0 !important;
            }

            .show-on-focus {
                position: absolute !important;
            }

            .skip-to-content {
                z-index: 99999;
            }

            button {
                color: var(--ak-dark-foreground);
                z-index: 99999;
                background-color: var(--ak-accent);
                font-family: var(--pf-global--FontFamily--heading--sans-serif);
                padding: var(--pf-global--spacer--md);
            }
        `,
    ];

    @property({ type: String })
    public flowTo: string = "main-content";

    #skipToContent = () => {
        const element =
            this.parentElement?.querySelector<HTMLElement>(`#${this.flowTo}`) ||
            document.getElementById(this.flowTo);

        if (!element) {
            console.warn(`Could not find element with ID "${this.flowTo}"`);
            return;
        }

        element.scrollIntoView();
        element.focus?.();
    };

    render() {
        return html`
            <button
                @click=${this.#skipToContent}
                type="button"
                class="show-on-focus js-skip-to-content"
            >
                ${msg("Skip to content")}
            </button>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-skip-to-content": AKSkipToContent;
    }
}
