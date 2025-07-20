import { AKElement } from "#elements/Base";

import { css, html } from "lit";
import { customElement } from "lit/decorators.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

@customElement("ak-wizard-title")
export class AkWizardTitle extends AKElement {
    static styles = [
        PFContent,
        PFTitle,
        css`
            .ak-bottom-spacing {
                padding-bottom: var(--pf-global--spacer--lg);
            }
        `,
    ];

    render() {
        return html`<div class="ak-bottom-spacing pf-c-content">
            <h3 data-test-id="wizard-heading"><slot></slot></h3>
        </div>`;
    }
}

export default AkWizardTitle;

declare global {
    interface HTMLElementTagNameMap {
        "ak-wizard-title": AkWizardTitle;
    }

    interface WizardTestIDMap {
        heading: HTMLHeadingElement;
    }

    interface TestIDSelectorMap {
        wizard: WizardTestIDMap;
    }
}
