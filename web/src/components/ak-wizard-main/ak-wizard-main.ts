import { AKElement } from "@goauthentik/elements/Base";
import { CustomListenerElement } from "@goauthentik/elements/utils/eventEmitter";

import { provide } from "@lit-labs/context";
import { html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import "./ak-wizard-frame";
import { akWizardCurrentStepContextName } from "./akWizardCurrentStepContextName";
import { akWizardStepsContextName } from "./akWizardStepsContextName";
import type { WizardStep } from "./types";

/**
 * AKWizardMain
 *
 * @element ak-wizard-main
 *
 * This is the entry point for the wizard.  Its tasks are:
 * - keep the collection of steps
 * - maintain the open/close status of the modal
 * - listens for navigation events
 * - if a navigation event is valid, switch to the panel requested
 */

@customElement("ak-wizard-main")
export class AkWizardMain extends CustomListenerElement(AKElement) {
    static get styles() {
        return [PFBase, PFButton, PFRadio];
    }

    @property()
    eventName: string = "ak-wizard-nav";

    /**
     * The steps of the Wizard.
     *
     * @attribute
     */
    @provide({ context: akWizardStepsContextName })
    @property({ attribute: false })
    steps: WizardStep[] = [];

    /**
     * The current step of the wizard.
     *
     * @attribute
     */
    @provide({ context: akWizardCurrentStepContextName })
    @state()
    currentStep!: WizardStep;

    constructor() {
        super();
        this.handleNavigation = this.handleNavigation.bind(this);
    }

    /**
     * The text of the modal button
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

    // Guarantee that if the current step was not passed in by the client, that we know
    // and set to the first step.
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    willUpdate(_changedProperties: Map<string, any>) {
        if (this.currentStep === undefined) {
            this.currentStep = this.steps[0];
        }
    }

    connectedCallback() {
        super.connectedCallback();
        this.addCustomListener(this.eventName, this.handleNavigation);
    }

    disconnectedCallback() {
        this.removeCustomListener(this.eventName, this.handleNavigation);
        super.disconnectedCallback();
    }

    // Note that we always scan for the valid next step and throw an error if we can't find it.
    // There should never be a question that the currentStep is a *valid* step.
    //
    // TODO: Put a phase in there so that the current step can validate the contents asynchronously
    // before setting the currentStep. Especially since setting the currentStep triggers a second
    // asynchronous event-- scheduling a re-render of everything interested in the currentStep
    // object.
    handleNavigation(event: CustomEvent<{ step: string }>) {
        const requestedStep = event.detail.step;
        if (!requestedStep) {
            throw new Error("Request for next step when no next step is available");
        }
        const step = this.steps.find(({ id }) => id === requestedStep);
        if (!step) {
            throw new Error("Request for next step when no next step is available.");
        }
        if (step.disabled) {
            throw new Error("Request for next step when the next step is disabled.");
        }
        this.currentStep = step;
        return;
    }

    render() {
        return html`
            <ak-wizard-frame
                ?open=${this.open}
                header=${this.header}
                description=${ifDefined(this.description)}
                eventName=${this.eventName}
            >
                <button slot="trigger" class="pf-c-button pf-m-primary">${this.prompt}</button>
            </ak-wizard-frame>
        `;
    }
}

export default AkWizardMain;
