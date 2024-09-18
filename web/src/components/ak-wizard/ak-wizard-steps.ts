import { AKElement } from "@goauthentik/elements/Base.js";
import { bound } from "@goauthentik/elements/decorators/bound";

import { ContextProvider } from "@lit/context";
import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import { wizardStepContext } from "./WizardContexts";
import { type WizardStep } from "./WizardStep";
import { WizardNavigationEvent } from "./events";
import { WizardStepState } from "./types";

/**
 * @class WizardStepsManager
 * @component ak-wizard-Steps
 *
 * This class keeps *all* the steps of the wizard, and knows the identity of the "current" step.
 * When a navigation event reaches it, it changes the view to show that step. It can determine the
 * slot names and identities dynamically from the slot names of its immediate children, and will
 * recalculate the slots if the component using this class changes them.
 *
 */

@customElement("ak-wizard-steps")
export class WizardStepsManager extends AKElement {
    @property({ type: String, attribute: true })
    currentStep?: string;

    @property({ type: Array, attribute: false })
    enabled: string[] = [];

    wizardStepContext!: ContextProvider<{ __context__: WizardStepState | undefined }>;

    slots: WizardStep[] = [];

    constructor() {
        super();
        this.wizardStepContext = new ContextProvider(this, {
            context: wizardStepContext,
            initialValue: {
                currentStep: undefined,
                stepLabels: [],
            },
        });
        this.addEventListener(WizardNavigationEvent.eventName, this.onNavigation);
        this.addEventListener("slotchange", this.onSlotchange);
    }

    findSlots() {
        this.slots = Array.from(this.querySelectorAll("[slot]"));
    }

    get stepLabels() {
        return this.slots
            .filter((slot) => !slot.hidden)
            .map((slot) => ({
                label: slot.label,
                id: slot.slot,
                active: true,
                enabled: slot.enabled,
            }));
    }

    findStepLabels() {
        this.wizardStepContext.setValue({
            ...this.wizardStepContext.value,
            stepLabels: this.stepLabels,
        });
    }

    connectedCallback() {
        super.connectedCallback();
        this.findSlots();
        this.findStepLabels();
        if (!this.currentStep && this.slots.length > 0) {
            const currentStep = this.slots[0].getAttribute("slot");
            if (!currentStep) {
                throw new Error("All steps managed by this component must have a slot definition.");
            }
            this.currentStep = currentStep;
            this.wizardStepContext.setValue({
                stepLabels: this.stepLabels,
                currentStep: currentStep,
            });
        }
    }

    @bound
    onSlotchange(ev: Event) {
        ev.stopPropagation();
        this.findSlots();
        if (!this.slots.find((slot) => slot.id === this.currentStep)) {
            throw new Error(`Slot update caused currentStep ${this.currentStep} to be invalid.`);
        }
        this.findStepLabels();
    }

    @bound
    onNavigation(ev: WizardNavigationEvent) {
        ev.stopPropagation();
        const { destination } = ev;
        // This overcomes a scheduling bug where native events can be asynchronous, resulting in the
        // delivery of enabling messages happening after the delivery of navigation messages.
        const target = this.slots.find((slot) => slot.slot === destination);
        if (!target) {
            throw new Error(`Attempted to navigate to unknown step: ${destination}`);
        }
        target.enabled = true;
        this.currentStep = target.slot;
        this.wizardStepContext.setValue({
            stepLabels: this.stepLabels,
            currentStep: target.slot,
        });
    }

    render() {
        return this.currentStep ? html`<slot name=${this.currentStep}></slot>` : nothing;
    }

    firstUpdated() {
        this.findStepLabels();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-wizard-steps": WizardStepsManager;
    }
}
