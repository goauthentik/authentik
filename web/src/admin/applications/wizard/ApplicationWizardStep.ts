import { styles } from "@goauthentik/admin/applications/wizard/ApplicationWizardFormStepStyles.css.js";
import { WizardStep } from "@goauthentik/components/ak-wizard/WizardStep.js";
import {
    NavigationEventInit,
    WizardNavigationEvent,
    WizardUpdateEvent,
} from "@goauthentik/components/ak-wizard/events";
import { KeyUnknown, serializeForm } from "@goauthentik/elements/forms/Form";
import { HorizontalFormElement } from "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { property, query } from "lit/decorators.js";

import { ValidationError } from "@goauthentik/api";

import {
    ApplicationTransactionValidationError,
    type ApplicationWizardState,
    type ApplicationWizardStateUpdate,
} from "./types";

export class ApplicationWizardStep extends WizardStep {
    static get styles() {
        return [...WizardStep.styles, ...styles];
    }

    @property({ type: Object, attribute: false })
    wizard!: ApplicationWizardState;

    // As recommended in [WizardStep](../../../components/ak-wizard/WizardStep.ts), we override
    // these fields and provide them to all the child classes.
    wizardTitle = msg("New application");
    wizardDescription = msg("Create a new application and configure a provider for it.");
    canCancel = true;

    // This should be overridden in the children for more precise targeting.
    @query("form")
    form!: HTMLFormElement;

    get formValues(): KeyUnknown | undefined {
        const elements = [
            ...Array.from(
                this.form.querySelectorAll<HorizontalFormElement>("ak-form-element-horizontal"),
            ),
            ...Array.from(this.form.querySelectorAll<HTMLElement>("[data-ak-control=true]")),
        ];
        return serializeForm(elements as unknown as NodeListOf<HorizontalFormElement>);
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
