import { AKElement } from "@goauthentik/elements/Base";
import { RadioOption } from "@goauthentik/elements/forms/Radio";

import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

type AkRadioArgs<T> = {
    // The name of the field, snake-to-camel'd if necessary.
    name: string;
    // The label of the field.
    label: string;
    value?: T;
    required?: boolean;
    options: RadioOption<T>[];
    // The help message, shown at the bottom.
    help?: string;
};

const akRadioDefaults = {
    required: false,
    options: [],
};

export function akRadioInput<T>(args: AkRadioArgs<T>) {
    const { name, label, help, required, options, value } = {
        ...akRadioDefaults,
        ...args,
    };

    return html`<ak-form-element-horizontal label=${label} ?required=${required} name=${name}>
        <ak-radio .options=${options} .value=${value}></ak-radio>
        ${help ? html`<p class="pf-c-form__helper-radio">${help}</p>` : nothing}
    </ak-form-element-horizontal> `;
}

@customElement("ak-radio-input")
export class AkRadioInput<T> extends AKElement {
    // Render into the lightDOM. This effectively erases the shadowDOM nature of this component, but
    // we're not actually using that and, for the meantime, we need the form handlers to be able to
    // find the children of this component.
    //
    // TODO: This abstraction is wrong; it's putting *more* layers in as a way of managing the
    // visual clutter and legibility issues of ak-form-elemental-horizontal and patternfly in
    // general.
    protected createRenderRoot() {
        return this;
    }

    @property({ type: String })
    name!: string;

    @property({ type: String })
    label = "";

    @property({ type: String })
    help = "";

    @property({ type: Boolean })
    required = false;

    @property({ type: Object })
    value!: T;

    @property({ type: Array })
    options: RadioOption<T>[] = [];

    render() {
        return akRadioInput({
            name: this.name,
            label: this.label,
            value: this.value,
            options: this.options,
            required: this.required,
            help: this.help.trim() !== "" ? this.help : undefined,
        });
    }
}

export default AkRadioInput;
