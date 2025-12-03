import "#components/ak-number-input";
import "#components/ak-radio-input";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";

import { styles as AwadStyles } from "../../ApplicationWizardFormStepStyles.styles.js";

import { AKElement } from "#elements/Base";
import { serializeForm } from "#elements/forms/Form";

import type { OneOfProvider } from "#admin/applications/wizard/steps/providers/shared";
import type { ApplicationWizardState } from "#admin/applications/wizard/types";

import { snakeCase } from "change-case";

import { CSSResult } from "lit";
import { property, query } from "lit/decorators.js";

export abstract class ApplicationWizardProviderForm<T extends OneOfProvider> extends AKElement {
    static styles: CSSResult[] = [...AwadStyles];

    abstract label: string;

    @property({ type: Object, attribute: false })
    wizard!: ApplicationWizardState<T>;

    @property({ type: Object, attribute: false })
    errors: Record<string | number | symbol, string> = {};

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
        this.errors = {};

        return !!this.form?.checkValidity();
    }

    errorMessages(name: string) {
        return name in this.errors
            ? [this.errors[name]]
            : (this.wizard.errors?.provider?.[name] ??
                  this.wizard.errors?.provider?.[snakeCase(name)] ??
                  []);
    }

    isValid(name: keyof T) {
        return !(
            (this.wizard.errors?.provider?.[name as string] ?? []).length > 0 ||
            this.errors?.[name] !== undefined
        );
    }
}
