import "#components/ak-number-input";
import "#components/ak-radio-input";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";

import { AKElement } from "#elements/Base";
import { serializeForm } from "#elements/forms/Form";

import { ApplicationWizardStyles } from "#admin/applications/wizard/ApplicationWizardFormStepStyles.styles";
import {
    AppliationWizardStateError,
    ApplicationTransactionValidationError,
    type ApplicationWizardState,
    type OneOfProvider,
} from "#admin/applications/wizard/steps/providers/shared";

import { snakeCase } from "change-case";

import { CSSResult } from "lit";
import { property, query } from "lit/decorators.js";

export abstract class ApplicationWizardProviderForm<
    P extends OneOfProvider,
    E extends AppliationWizardStateError = ApplicationTransactionValidationError,
> extends AKElement {
    static styles: CSSResult[] = [...ApplicationWizardStyles];

    public abstract label: string;

    @property({ type: Object, attribute: false })
    public wizard!: ApplicationWizardState<P, E>;

    @property({ type: Object, attribute: false })
    public errors: E = {} as E;

    @query("form#providerform")
    public form!: HTMLFormElement | null;

    get formValues() {
        if (!this.form) {
            throw new TypeError("Form reference is not set");
        }

        return serializeForm([
            ...this.form.querySelectorAll("ak-form-element-horizontal"),
            ...this.form.querySelectorAll("[data-ak-control]"),
        ]);
    }

    get valid() {
        this.errors = {} as E;

        return !!this.form?.checkValidity();
    }

    errorMessages<T extends Extract<keyof E, string>>(name: T): Array<E[T]> {
        if (name in this.errors) {
            return [this.errors[name]];
        }

        return (
            this.wizard.errors?.provider?.[name] ??
            this.wizard.errors?.provider?.[snakeCase(name) as keyof E] ??
            []
        );
    }
}
