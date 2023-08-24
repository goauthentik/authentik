import { AKElement } from "@goauthentik/elements/Base";
import { CustomListenerElement } from "@goauthentik/elements/utils/eventEmitter";

import { html } from "lit";
import { customElement, property, query, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import "./ak-wizard-frame";
import { AkWizardFrame } from "./ak-wizard-frame";
import type { WizardPanel, WizardStep } from "./types";

// Not just a check that it has a validator, but a check that satisfies Typescript that we're using
// it correctly; anything within the hasValidator conditional block will know it's dealing with
// a fully operational WizardPanel.
//
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const hasValidator = (v: any): v is Required<Pick<WizardPanel, "validator">> =>
    "validator" in v && typeof v.validator === "function";

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
    @property({ attribute: false })
    steps: WizardStep[] = [];

    /**
     * The current step of the wizard.
     *
     * @attribute
     */
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

    @query("ak-wizard-frame")
    frame!: AkWizardFrame;

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
    handleNavigation(event: CustomEvent<{ step: string; action: string }>) {
        const requestedStep = event.detail.step;
        if (!requestedStep) {
            throw new Error("Request for next step when no next step is available");
        }
        const step = this.steps.find(({ id }) => id === requestedStep);
        if (!step) {
            throw new Error("Request for next step when no next step is available.");
        }
        if (event.detail.action === "next" && !this.validated()) {
            return false;
        }
        this.currentStep = step;
        return true;
    }

    validated() {
        if (hasValidator(this.frame.content)) {
            return this.frame.content.validator();
        }
        return true;
    }

    render() {
        return html`
            <ak-wizard-frame
                ?open=${this.open}
                header=${this.header}
                description=${ifDefined(this.description)}
                eventName=${this.eventName}
                .steps=${this.steps}
                .currentStep=${this.currentStep}
            >
                <button slot="trigger" class="pf-c-button pf-m-primary">${this.prompt}</button>
            </ak-wizard-frame>
        `;
    }
}

export default AkWizardMain;
