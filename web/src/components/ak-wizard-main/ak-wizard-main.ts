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
 * This is the controller for a multi-form wizard. It provides an interface for describing a pop-up
 * (modal) wizard, the contents of which are independent of the navigation. This controller only
 * handles the navigation.
 *
 * Each step (see the `types.ts` file) provides label, a "currently valid" boolean, a "disabled"
 * boolean, a function that returns the HTML of the object to be rendered, a `disabled` flag
 * indicating

 Its tasks are:
 * - keep the collection of steps
 * - maintain the open/close status of the modal
 * - listens for navigation events
 * - if a navigation event is valid, switch to the panel requested
 *
 * 
 
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
    currentStep: number = 0;

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

    /**
     * Whether or not to show the "cancel" button in the wizard.
     *
     * @attribute
     */
    @property({ type: Boolean })
    canCancel!: boolean;

    @query("ak-wizard-frame")
    frame!: AkWizardFrame;

    connectedCallback() {
        super.connectedCallback();
        this.addCustomListener(this.eventName, this.handleNavigation);
    }

    disconnectedCallback() {
        this.removeCustomListener(this.eventName, this.handleNavigation);
        super.disconnectedCallback();
    }

    get maxStep() {
        return this.steps.length - 1;
    }

    get nextStep() {
        return this.currentStep < this.maxStep ? this.currentStep + 1 : undefined;
    }

    get backStep() {
        return this.currentStep > 0 ? this.currentStep - 1 : undefined;
    }

    get step() {
        return this.steps[this.currentStep];
    }

    handleNavigation(event: CustomEvent<{ command: string; step?: number }>) {
        const command = event.detail.command;
        switch (command) {
            case "back": {
                if (this.backStep !== undefined && this.steps[this.backStep]) {
                    this.currentStep = this.backStep;
                }
                return;
            }
            case "goto": {
                if (
                    typeof event.detail.step === "number" &&
                    event.detail.step >= 0 &&
                    event.detail.step <= this.maxStep
                )
                    this.currentStep = event.detail.step;
                return;
            }
            case "next": {
                console.log(this.nextStep, 
                    this.steps[this.nextStep], 
                    !this.steps[this.nextStep].disabled, 
                    this.validated);
                
                if (
                    this.nextStep &&
                    this.steps[this.nextStep] &&
                    !this.steps[this.nextStep].disabled &&
                    this.validated
                ) {
                    this.currentStep = this.nextStep;
                }
                return;
            }
            case "close": {
                this.frame.open = false;
            }
        }
    }

    get validated() {
        if (hasValidator(this.frame.content)) {
            return this.frame.content.validator();
        }
        return true;
    }

    render() {
        return html`
            <ak-wizard-frame
                ?canCancel=${this.canCancel}
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
