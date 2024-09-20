import "@goauthentik/components/ak-number-input";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import { AKElement } from "@goauthentik/elements/Base.js";
import { KeyUnknown, serializeForm } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { HorizontalFormElement } from "@goauthentik/elements/forms/HorizontalFormElement";

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
    errors: Map<string | number | symbol, string> = new Map();

    @query("form#providerform")
    form!: HTMLFormElement;

    get formValues(): KeyUnknown | undefined {
        const elements = [
            ...Array.from(
                this.form.querySelectorAll<HorizontalFormElement>("ak-form-element-horizontal")
            ),
            ...Array.from(this.form.querySelectorAll<HTMLElement>("[data-ak-control=true]")),
        ];
        return serializeForm(elements as unknown as NodeListOf<HorizontalFormElement>);
    }

    get valid() {
        this.errors = new Map();
        return this.form.checkValidity();
    }

    errorMessages(name: keyof T) {
        if (name in (this.wizard.errors?.provider ?? {})) {
            return this.wizard.errors?.provider[name];
        }
        return this.errors.has(name) ? [this.errors.get(name)] : [];
    }

    isValid(name: keyof T) {
        return !((this.wizard.errors.provider[name] ?? []).length > 0 || this.errors.has(name));
    }
}
