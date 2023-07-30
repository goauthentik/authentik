import { msg } from "@lit/localize";
import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

type AkTextInput = {
    // The name of the field, snake-to-camel'd if necessary.
    name: string;
    // The label of the field.
    label: string;
    value?: any;
    required: boolean;
    // The help message, shown at the bottom.
    help?: string;
};

const akTextDefaults = {
    required: false,
};

export function akText(args: AkTextInput) {
    const { name, label, value, required, help } = {
        ...akTextDefaults,
        ...args
    }
    
    return html`<ak-form-element-horizontal label=${label} ?required=${required} name=${name}>
        <input
            type="text"
            value=${ifDefined(value)}
            class="pf-c-form-control"
            ?required=${required}
        />
        <p class="pf-c-form__helper-text">${help}</p>
    </ak-form-element-horizontal> `;
}
