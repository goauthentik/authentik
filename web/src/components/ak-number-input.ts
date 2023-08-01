import { AKElement } from "@goauthentik/elements/Base";

import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

type AkNumberArgs = {
    // The name of the field, snake-to-camel'd if necessary.
    name: string;
    // The label of the field.
    label: string;
    value?: number;
    required: boolean;
    // The help message, shown at the bottom.
    help?: string;
};

const akNumberDefaults = {
    required: false,
};

export function akNumber(args: AkNumberArgs) {
    const { name, label, value, required, help } = {
        ...akNumberDefaults,
        ...args,
    };

    return html`<ak-form-element-horizontal label=${label} ?required=${required} name=${name}>
        <input
            type="number"
            value=${ifDefined(value)}
            class="pf-c-form-control"
            ?required=${required}
        />
        ${help ? html`<p class="pf-c-form__helper-text">${help}</p>` : nothing}
    </ak-form-element-horizontal> `;
}

@customElement("ak-number-input")
export class AkNumberInput extends AKElement {
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

    @property({ type: Number })
    value = 0;

    @property({ type: Boolean })
    required = false;

    @property({ type: String })
    help = "";

    render() {
        return akNumber({
            name: this.name,
            label: this.label,
            value: this.value,
            required: this.required,
            help: this.help.trim() !== "" ? this.help : undefined,
        });
    }
}
