import { CustomListenerElement } from "@goauthentik/elements/utils/eventEmitter";

import { provide } from "@lit-labs/context";
import { customElement, property, state } from "@lit/reactive-element/decorators.js";
import { LitElement, html } from "lit";

import type { WizardStep, WizardStepId } from "./types";
import { WizardStepEvent, } from "./types";
import { akWizardCurrentStepContextName } from "./akWizardCurrentStepContextName";
import { akWizardStepsContextName } from "./akWizardStepsContextName";

/**
 * AkWizardContext
 *
 * @element ak-wizard-context
 *
 * The WizardContext controls the navigation for the wizard. It listens for navigation events from
 * the wizard frame and responds with changes to the view, including handling the close button.
 *
 */

@customElement("ak-wizard-context") 
export class AkWizardContext extends CustomListenerElement(LitElement) {

    @property()
    eventName: string = "ak-wizard-nav";
    
    @provide({ context: akWizardStepsContextName })
    @property({ attribute: false })
    steps: WizardStep[] = [];

    @provide({ context: akWizardCurrentStepContextName })
    @state()
    currentStep!: WizardStep;

    constructor() {
        super();
        this.handleNavigation = this.handleNavigation.bind(this);
    }

    // This is the only case where currentStep could be anything other than a valid entry. Unless,
    // of course, a step itself is so badly messed up it can't point to a real object.
    willUpdate(_changedProperties: Map<string, any>) {
        if (this.currentStep === undefined) {
            this.currentStep = this.steps[0];
        }
    }

    // Note that we always scan for the valid next step and throw an error if we can't find it.
    // There should never be a question that the currentStep is a *valid* step.
    //
    // TODO: Put a phase in there so that the current step can validate the contents asynchronously
    // before setting the currentStep. Especially since setting the currentStep triggers a second
    // asynchronous event-- scheduling a re-render of everything interested in the currentStep
    // object.
    handleNavigation(event: CustomEvent<{ step: WizardStepId | WizardStepEvent }>) {
        const requestedStep = event.detail.step;
        if (!requestedStep) {
            throw new Error("Request for next step when no next step is available")
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

    connectedCallback() {
        super.connectedCallback();
        this.addCustomListener(this.eventName, this.handleNavigation);
    }

    disconnectedCallback() {
        this.removeCustomListener(this.eventName, this.handleNavigation);
        super.disconnectedCallback();
    }

    render() {
        return html`<slot></slot>`;
    }
}
