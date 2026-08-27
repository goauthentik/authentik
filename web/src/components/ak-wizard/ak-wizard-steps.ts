import { NavigationEventInit, WizardNavigationEvent } from "./events.js";
import { WizardStepLabel } from "./shared.js";
import { wizardStepContext } from "./WizardContexts.js";
import { type WizardStep } from "./WizardStep.js";

import { AKElement } from "#elements/Base";
import { listen } from "#elements/decorators/listen";

import { ContextProvider } from "@lit/context";
import { css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

const asArr = (v?: string[] | string) => {
    return typeof v === "undefined" ? [] : Array.isArray(v) ? v : [v];
};

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
    public static styles = [
        css`
            :host {
                display: contents;
            }
        `,
    ];

    @property({ type: String, attribute: true })
    public currentStep: string | null = null;

    protected slotMap: ReadonlyMap<string, WizardStep> = new Map();
    protected wizardStepContext = new ContextProvider(this, {
        context: wizardStepContext,
        initialValue: {
            currentStep: null,
            stepLabels: [],
        },
    });

    protected refreshSlots() {
        const nextSlots = new Map<string, WizardStep>();

        for (const slot of Array.from(this.querySelectorAll<WizardStep>("[slot]"))) {
            const name = slot.getAttribute("slot") ?? "";

            if (nextSlots.has(name)) {
                throw new Error(`Duplicate wizard step slot name detected: ${name}`);
            }

            nextSlots.set(name, slot);
        }

        this.slotMap = nextSlots;
    }

    protected get stepLabels(): WizardStepLabel[] {
        return Array.from(this.slotMap.values())
            .filter((slot) => !slot.hide)
            .map((slot) => ({
                label: slot.label,
                id: slot.slot,
                enabled: slot.enabled,
            }));
    }

    protected refreshStepLabels() {
        this.wizardStepContext.setValue({
            ...this.wizardStepContext.value,
            stepLabels: this.stepLabels,
        });
    }

    public override connectedCallback() {
        super.connectedCallback();

        this.refreshSlots();
        this.refreshStepLabels();

        if (!this.currentStep) {
            const [firstEntry] = this.slotMap;

            if (!firstEntry) {
                throw new Error(
                    "No current step set on wizard steps manager, and no steps found in slots.",
                );
            }

            const [currentStep] = firstEntry;

            this.currentStep = currentStep;

            this.wizardStepContext.setValue({
                stepLabels: this.stepLabels,
                currentStep,
            });
        }
    }

    public override firstUpdated() {
        this.refreshStepLabels();
    }

    protected findSlot(name: string | null): WizardStep {
        const slot = this.slotMap.get(name ?? "");

        if (!slot) {
            throw new Error(`Could not find step with slot name ${name}`);
        }

        return slot;
    }

    protected refresh = (event: Event) => {
        event.stopPropagation();

        this.refreshSlots();

        this.findSlot(this.currentStep);

        this.refreshStepLabels();
    };

    /**
     * This event sequence handles the following possibilities:
     *
     * - The user on a step validated and wants to move forward. We want to make sure the *next*
     *   step in enabled.
     * - The user went *back* and changed a step and it is no longer valid. We want to disable all
     *   future steps until that is corrected. Yes, in this case the flow is "Now you have to go
     *   through the entire wizard," but since the user invalidated a prior, that shouldn't be
     *   unexpected.  None of the data will have been lost.
     */
    protected updateStepAvailability(details: NavigationEventInit) {
        const enabled = asArr(details.enable);

        enabled.forEach((name) => {
            this.findSlot(name).enabled = true;
        });

        if (details.disabled) {
            const disabled = asArr(details.disabled);
            this.slotMap.forEach((slot) => {
                slot.enabled = !disabled.includes(slot.slot);
            });
        }

        if (details.hidden) {
            const hidden = asArr(details.hidden);
            this.slotMap.forEach((slot) => {
                slot.hide = hidden.includes(slot.slot);
            });
        }
    }

    @listen(WizardNavigationEvent)
    protected synchronizeContext = (event: WizardNavigationEvent) => {
        event.stopPropagation();

        const { destination, details } = event;

        if (details) {
            this.updateStepAvailability(details);
        }

        if (!destination) {
            return;
        }

        const target = this.slotMap.get(destination);

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
    };

    protected override render() {
        return this.currentStep ? html`<slot name=${this.currentStep}></slot>` : nothing;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-wizard-steps": WizardStepsManager;
    }
}
