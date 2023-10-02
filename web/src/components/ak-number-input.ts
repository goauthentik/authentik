import { AKElement } from "@goauthentik/elements/Base";

import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

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

    @property({ type: Number, reflect: true })
    value = 0;

    @property({ type: Boolean })
    required = false;

    @property({ type: String })
    help = "";

    render() {
        return html`<ak-form-element-horizontal
            label=${this.label}
            ?required=${this.required}
            name=${this.name}
        >
            <input
                type="number"
                value=${ifDefined(this.value)}
                class="pf-c-form-control"
                ?required=${this.required}
            />
            ${this.help ? html`<p class="pf-c-form__helper-text">${this.help}</p>` : nothing}
        </ak-form-element-horizontal> `;
    }
}

export default AkNumberInput;
