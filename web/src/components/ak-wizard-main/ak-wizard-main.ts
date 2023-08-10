import { AKElement } from "@goauthentik/elements/Base";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html } from "lit";
import { property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import "./ak-wizard-context";
import "./ak-wizard-frame";
import type { WizardStep } from "./types";

/**
 * AKWizardMain
 *
 * @element ak-wizard-main
 *
 * This is the entry point for the wizard.
 *
 */

@customElement("ak-wizard-main")
export class AkWizardMain extends AKElement {
    static get styles() {
        return [PFBase, PFButton, PFRadio];
    }

    /**
     * The steps of the Wizard.
     *
     * @attribute
     */
    @property({ attribute: false })
    steps: WizardStep[] = [];

    /**
     * The text of the button
     *
     * @attribute
     */
    @property({ type: String })
    prompt = "Show Wizard";

    /**
     * Mostly a control on the ModalButton that summons the wizard component.
     *
     * @attribute
     */
    @property({ type: Boolean, reflect: true })
    open = false;

    /**
     * The text of the header on the wizard, upper bar.
     *
     * @attribute
     */
    @property()
    header!: string;

    /**
     * The text of the description under the header.
     *
     * @attribute
     */
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
                    <button slot="trigger" class="pf-c-button pf-m-primary">${this.prompt}</button>
                </ak-wizard-frame>
            </ak-wizard-context>
        `;
    }
}

export default AkWizardMain;
