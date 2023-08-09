import { AKElement } from "@goauthentik/elements/Base";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html } from "lit";
import { property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import "../ak-wizard-context";
import "../ak-wizard-2";
import type { WizardStep } from "../types";

@customElement("ak-demo-wizard")
export class AkDemoWizard extends AKElement {
    static get styles() {
        return [PFBase, PFButton, PFRadio];
    }

    @property({ attribute: false })
    steps: WizardStep[] = [];

    @property({ type: Boolean })
    open = false;

    render() {
        return html`
            <ak-wizard-context .steps=${this.steps}>
                <ak-wizard-2
                    ?open=${this.open}
                    header=${"Demo Wizard"}
                    description=${"Just Showing Off The Demo Wizard"}
                >
                    <button slot="trigger" class="pf-c-button pf-m-primary">Show Wizard</button>
                </ak-wizard-2>
            </ak-wizard-context>
        `;
    }
}
