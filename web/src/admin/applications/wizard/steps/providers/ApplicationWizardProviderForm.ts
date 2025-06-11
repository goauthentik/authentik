import "@goauthentik/components/ak-number-input";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import { AKElement } from "@goauthentik/elements/Base.js";
import type { AkControlElement } from "@goauthentik/elements/forms/Form";
import { serializeForm } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { HorizontalFormElement } from "@goauthentik/elements/forms/HorizontalFormElement";
import { snakeCase } from "change-case";

import { property, query } from "lit/decorators.js";

import { styles as AwadStyles } from "../../ApplicationWizardFormStepStyles.css.js";
import { type ApplicationWizardState, type OneOfProvider } from "../../types";

export class ApplicationWizardProviderForm<T extends OneOfProvider> extends AKElement {
    static get styles() {
        return AwadStyles;
    }

    label = "";

    @property({ type: Object, attribute: false })
    wizard!: ApplicationWizardState;

    @property({ type: Object, attribute: false })
    errors: Record<string | number | symbol, string> = {};

    @query("form#providerform")
    form!: HTMLFormElement;

    get formValues(): Record<string, unknown> {
        const elements = [
            ...this.form.querySelectorAll<HorizontalFormElement>("ak-form-element-horizontal"),
            ...this.form.querySelectorAll<AkControlElement>("[data-ak-control]"),
        ];

        return serializeForm(elements);
    }

    get valid() {
        this.errors = {};
        return this.form.checkValidity();
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
