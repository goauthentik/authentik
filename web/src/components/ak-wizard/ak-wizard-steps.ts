import { NavigationEventInit, WizardNavigationEvent } from "./events.js";
import { WizardStepLabel, WizardStepState } from "./types.js";
import { wizardStepContext } from "./WizardContexts.js";
import { type WizardStep } from "./WizardStep.js";

import { AKElement } from "#elements/Base";
import { bound } from "#elements/decorators/bound";

import { Context, ContextProvider } from "@lit/context";
import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

/**
 * @class WizardStepsManager
 * @component ak-wizard-Steps
 *
 * This class keeps *all* the steps of the wizard, and knows the identity of the "current" step.
 * When a navigation event reaches it, it changes the view to show that step. Optionally, it can
 * process a "details" object from the WizardNavigationEvent that assigns enabled/disabled flags to
 * children that inherit from WizardStep. It can determine the slot names and identities dynamically
 * from the slot names of its immediate children, and will recalculate the slots if the component
 * using this class changes them.
 *
 */

@customElement("ak-wizard-steps")
export class WizardStepsManager extends AKElement {
    @property({ type: String, attribute: true })
    public currentStep?: string;

    protected wizardStepContext!: ContextProvider<Context<symbol, WizardStepState>>;

    protected slots: WizardStep[] = [];

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
        this.slots = Array.from(this.querySelectorAll("[slot]")) as WizardStep[];
    }

    findSlot(name?: string) {
        const target = this.slots.find((slot) => slot.slot === name);
        if (!target) {
            throw new Error(`Request for wizard panel that does not exist: ${name}`);
        }
        return target;
    }

    get stepLabels(): WizardStepLabel[] {
        return this.slots
            .filter((slot) => !slot.hide)
            .map((slot) => ({
                label: slot.label,
                id: slot.slot,
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
        this.findSlot(this.currentStep);
        this.findStepLabels();
    }

    // This event sequence handles the following possibilities:
    // - The user on a step validated and wants to move forward. We want to make sure the *next*
    //   step in enabled.
    // - The user went *back* and changed a step and it is no longer valid. We want to disable all
    //   future steps until that is corrected. Yes, in this case the flow is "Now you have to go
    //   through the entire wizard," but since the user invalidated a prior, that shouldn't be
    //   unexpected.  None of the data will have been lost.

    updateStepAvailability(details: NavigationEventInit) {
        const asArr = (v?: string[] | string) =>
            v === undefined ? [] : Array.isArray(v) ? v : [v];
        const enabled = asArr(details.enable);
        enabled.forEach((name) => {
            this.findSlot(name).enabled = true;
        });
        if (details.disabled !== undefined) {
            const disabled = asArr(details.disabled);
            this.slots.forEach((slot) => {
                slot.enabled = !disabled.includes(slot.slot);
            });
        }
        if (details.hidden !== undefined) {
            const hidden = asArr(details.hidden);
            this.slots.forEach((slot) => {
                slot.hide = hidden.includes(slot.slot);
            });
        }
    }

    @bound
    onNavigation(ev: WizardNavigationEvent) {
        ev.stopPropagation();
        const { destination, details } = ev;

        if (details) {
            this.updateStepAvailability(details);
        }

        if (!destination) {
            return;
        }

        const target = this.slots.find((slot) => slot.slot === destination);
        if (!target) {
            throw new Error(`Attempted to navigate to unknown step: ${destination}`);
        }
        if (!target.enabled) {
            throw new Error(`Attempted to navigate to disabled step: ${destination}`);
        }
        if (target.slot === this.currentStep) {
            return;
        }
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
