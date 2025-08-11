import {
    ApplicationTransactionValidationError,
    type ApplicationWizardState,
    type ApplicationWizardStateUpdate,
} from "./types.js";

import { serializeForm } from "#elements/forms/Form";

import {
    NavigationEventInit,
    WizardNavigationEvent,
    WizardUpdateEvent,
} from "#components/ak-wizard/events";
import { WizardStep } from "#components/ak-wizard/WizardStep";

import { styles } from "#admin/applications/wizard/ApplicationWizardFormStepStyles.styles";

import { ApplicationRequest, ValidationError } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { property, query } from "lit/decorators.js";

export class ApplicationWizardStep<T = Partial<ApplicationRequest>> extends WizardStep {
    static styles = [...WizardStep.styles, ...styles];

    @property({ type: Object, attribute: false })
    wizard!: ApplicationWizardState;

    // As recommended in [WizardStep](../../../components/ak-wizard/WizardStep.ts), we override
    // these fields and provide them to all the child classes.
    protected wizardTitle = msg("New application");
    protected wizardDescription = msg("Create a new application and configure a provider for it.");
    public canCancel = true;

    // This should be overridden in the children for more precise targeting.
    @query("form")
    protected form!: HTMLFormElement;

    protected get formValues(): T {
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
