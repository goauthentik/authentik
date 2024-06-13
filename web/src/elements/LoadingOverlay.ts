import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/EmptyState";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-loading-overlay")
export class LoadingOverlay extends AKElement {
    @property({ type: Boolean })
    topMost = false;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            css`
                :host {
                    display: flex;
                    height: 100%;
                    width: 100%;
                    justify-content: center;
                    align-items: center;
                    position: absolute;
                    background-color: var(--pf-global--BackgroundColor--dark-transparent-200);
                    z-index: 1;
                }
                :host([topMost]) {
                    z-index: 999;
                }
            `,
        ];
    }

    render(): TemplateResult {
        return html`<ak-empty-state ?loading="${true}">
            <slot name="body" slot="body"></slot>
        </ak-empty-state>`;
    }
}
