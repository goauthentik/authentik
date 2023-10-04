import { AKElement } from "@goauthentik/elements/Base";
import { RadioOption } from "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/Radio";

import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

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

    handleInput(ev: CustomEvent) {
        this.value = ev.detail.value;
    }

    render() {
        return html`<ak-form-element-horizontal
            label=${this.label}
            ?required=${this.required}
            name=${this.name}
        >
            <ak-radio
                .options=${this.options}
                .value=${this.value}
                @input=${this.handleInput}
            ></ak-radio>
            ${this.help.trim()
                ? html`<p class="pf-c-form__helper-radio">${this.help}</p>`
                : nothing}
        </ak-form-element-horizontal> `;
    }
}

export default AkRadioInput;
