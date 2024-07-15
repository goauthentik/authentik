import { AKElement } from "@goauthentik/elements/Base";

import { css, html } from "lit";
import { customElement } from "lit/decorators.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

@customElement("ak-wizard-title")
export class AkWizardTitle extends AKElement {
    static get styles() {
        return [
            PFContent,
            PFTitle,
            css`
                .ak-bottom-spacing {
                    padding-bottom: var(--pf-global--spacer--lg);
                }
            `,
        ];
    }

    render() {
        return html`<div class="ak-bottom-spacing pf-c-content">
            <h3><slot></slot></h3>
        </div>`;
    }
}

export default AkWizardTitle;

declare global {
    interface HTMLElementTagNameMap {
        "ak-wizard-title": AkWizardTitle;
    }
}
