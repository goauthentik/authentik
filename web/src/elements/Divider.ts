import { CSSResult, LitElement, TemplateResult, css, html } from "lit";
import { customElement } from "lit/decorators.js";

import AKGlobal from "@goauthentik/web/authentik.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-divider")
export class Divider extends LitElement {
    static get styles(): CSSResult[] {
        return [
            PFBase,
            AKGlobal,
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

    render(): TemplateResult {
        return html`<div class="separator"><slot></slot></div>`;
    }
}
