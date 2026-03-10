import { serializeForm } from "#elements/forms/Form";
import { reportValidityDeep } from "#elements/forms/FormGroup";

import {
    NavigationEventInit,
    WizardNavigationEvent,
    WizardUpdateEvent,
} from "#components/ak-wizard/events";
import { WizardStep } from "#components/ak-wizard/WizardStep";

import { ApplicationWizardStyles } from "#admin/applications/wizard/ApplicationWizardFormStepStyles.styles";
import {
    type ApplicationWizardState,
    type ApplicationWizardStateUpdate,
} from "#admin/applications/wizard/steps/providers/shared";

import { ApplicationRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { property } from "lit/decorators.js";

/**
 * Base class for application wizard steps. Provides common functionality such as form handling and wizard state management.
 *
 * @prop wizard - The current state of the application wizard, shared across all steps.
 */
export abstract class ApplicationWizardStep<T = Partial<ApplicationRequest>> extends WizardStep {
    static styles = [...WizardStep.styles, ...ApplicationWizardStyles];

    @property({ type: Object, attribute: false })
    public wizard!: ApplicationWizardState;

    protected override wizardTitle = msg("New application");
    protected override wizardDescription = msg(
        "Create a new application and configure a provider for it.",
    );
    public canCancel = true;

    // This should be overridden in the children for more precise targeting.
    public get form(): HTMLFormElement | null {
        return this.renderRoot.querySelector("form");
    }

    /**
     * @todo This defaults to true when the form is not yet available
     * to ease the migration of existing wizards. This behavior should be removed.
     */
    public reportValidity(): boolean {
        const { form } = this;

        if (!form) return true;

        return reportValidityDeep(form);
    }

    /**
     * @todo This defaults to true when the form is not yet available
     * to ease the migration of existing wizards. This behavior should be removed.
     */
    public checkValidity(): boolean {
        const { form } = this;

        if (!form) return true;

        return form.checkValidity();
    }

    protected get formValues(): T {
        if (!this.form) {
            throw new TypeError("Form reference is not set");
        }

        return serializeForm<T>([
            ...this.form.querySelectorAll("ak-form-element-horizontal"),
            ...this.form.querySelectorAll("[data-ak-control]"),
        ]);
    }

    // This pattern became visible during development, and the order is important: wizard updating
    // and validation must complete before navigation is attempted.
    public handleUpdate(
        update?: ApplicationWizardStateUpdate,
        destination?: string,
        enable?: NavigationEventInit,
    ) {
        // Inform ApplicationWizard of content state
        if (update) {
            this.dispatchEvent(new WizardUpdateEvent(update));
        }

        // Inform WizardStepManager of steps state
        if (destination || enable) {
            this.dispatchEvent(new WizardNavigationEvent(destination, enable));
        }
    }
}
