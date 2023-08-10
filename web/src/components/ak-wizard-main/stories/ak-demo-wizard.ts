import { AKElement } from "@goauthentik/elements/Base";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html } from "lit";
import { property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import "../ak-wizard-frame";
import "../ak-wizard-context";
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

    @property()
    header!: string;

    @property()
    description?: string;

    render() {
        return html`
            <ak-wizard-context .steps=${this.steps}>
                <ak-wizard-frame
                    ?open=${this.open}
                    header=${this.header}
                    description=${ifDefined(this.description)}
                >
                    <button slot="trigger" class="pf-c-button pf-m-primary">Show Wizard</button>
                </ak-wizard-frame>
            </ak-wizard-context>
        `;
    }
}
