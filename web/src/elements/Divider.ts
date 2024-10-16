import { AKElement } from "@goauthentik/elements/Base";
import { type SlottedTemplateResult } from "@goauthentik/elements/types";

import { css, html, nothing } from "lit";
import { customElement } from "lit/decorators.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-divider")
export class Divider extends AKElement {
    static get styles() {
        return [
            PFBase,
            css`
                .separator {
                    display: flex;
                    align-items: center;
                    text-align: center;
                }

                .separator::before,
                .separator::after {
                    content: "";
                    flex: 1;
                    border-bottom: 1px solid var(--pf-global--Color--100);
                }

                .separator:not(:empty)::before {
                    margin-right: 0.25em;
                }

                .separator:not(:empty)::after {
                    margin-left: 0.25em;
                }
            `,
        ];
    }

    render() {
        return html`<div class="separator">
            <slot></slot>
        </div>`;
    }
}

export function akDivider(content: SlottedTemplateResult = nothing) {
    const message = typeof content === "string" ? html`<span>${content}</span>` : content;
    return html`<ak-divider>${message}</ak-divider>`;
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-divider": Divider;
    }
}
