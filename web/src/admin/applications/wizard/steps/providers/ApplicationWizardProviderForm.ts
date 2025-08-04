import "#components/ak-number-input";
import "#components/ak-radio-input";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";

import { styles as AwadStyles } from "../../ApplicationWizardFormStepStyles.styles.js";
import { type ApplicationWizardState, type OneOfProvider } from "../../types.js";

import { camelToSnake } from "#common/utils";

import { AKElement } from "#elements/Base";
import { serializeForm } from "#elements/forms/Form";

import { CSSResult } from "lit";
import { property, query } from "lit/decorators.js";

export class ApplicationWizardProviderForm<T extends OneOfProvider> extends AKElement {
    public static override styles: CSSResult[] = [...AwadStyles];

    public label = "";

    @property({ type: Object, attribute: false })
    public wizard!: ApplicationWizardState;

    @property({ type: Object, attribute: false })
    public errors: Record<string | number | symbol, string> = {};

    @query("form#providerform")
    protected form!: HTMLFormElement;

    public get formValues() {
        return serializeForm([
            ...this.form.querySelectorAll("ak-form-element-horizontal"),
            ...this.form.querySelectorAll("[data-ak-control]"),
        ]);
    }

    public get valid() {
        this.errors = {};
        return this.form.checkValidity();
    }

    protected errorMessages(name: string) {
        return name in this.errors
            ? [this.errors[name]]
            : (this.wizard.errors?.provider?.[name] ??
                  this.wizard.errors?.provider?.[camelToSnake(name)] ??
                  []);
    }

    protected isValid(name: keyof T) {
        return !(
            (this.wizard.errors?.provider?.[name as string] ?? []).length > 0 ||
            this.errors?.[name] !== undefined
        );
    }
}
