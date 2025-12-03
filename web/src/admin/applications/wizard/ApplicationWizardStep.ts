import {
    ApplicationTransactionValidationError,
    type ApplicationWizardState,
    type ApplicationWizardStateUpdate,
} from "./types.js";

import { serializeForm } from "#elements/forms/Form";
import { reportValidityDeep } from "#elements/forms/FormGroup";

import {
    NavigationEventInit,
    WizardNavigationEvent,
    WizardUpdateEvent,
} from "#components/ak-wizard/events";
import { WizardStep } from "#components/ak-wizard/WizardStep";

import { styles } from "#admin/applications/wizard/ApplicationWizardFormStepStyles.styles";

import { ApplicationRequest, ValidationError } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { property } from "lit/decorators.js";

export class ApplicationWizardStep<
    T extends Partial<ApplicationRequest> = Partial<ApplicationRequest>,
> extends WizardStep {
    static styles = [...WizardStep.styles, ...styles];

    @property({ type: Object, attribute: false })
    wizard!: ApplicationWizardState<T>;

    // As recommended in [WizardStep](../../../components/ak-wizard/WizardStep.ts), we override
    // these fields and provide them to all the child classes.
    protected wizardTitle = msg("New application");
    protected wizardDescription = msg("Create a new application and configure a provider for it.");
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

    protected removeErrors(
        keyToDelete: keyof ApplicationTransactionValidationError,
    ): ValidationError | undefined {
        if (!this.wizard.errors) {
            return undefined;
        }
        const empty = {};
        const errors = Object.entries(this.wizard.errors).reduce(
            (acc, [key, value]) =>
                key === keyToDelete ||
                value === undefined ||
                (Array.isArray(this.wizard?.errors?.[key]) && this.wizard.errors[key].length === 0)
                    ? acc
                    : { ...acc, [key]: value },
            empty,
        );
        return errors;
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
