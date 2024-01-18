import { AKElement } from "@goauthentik/elements/Base";

import { html, nothing } from "lit";
import { customElement, property, query } from "lit/decorators.js";

@customElement("ak-switch-input")
export class AkSwitchInput extends AKElement {
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

    @property({ type: Boolean })
    checked: boolean = false;

    @property({ type: Boolean })
    required = false;

    @property({ type: String })
    help = "";

    @query("input.pf-c-switch__input[type=checkbox]")
    checkbox!: HTMLInputElement;

    render() {
        const doCheck = this.checked ? this.checked : undefined;

        return html` <ak-form-element-horizontal name=${this.name} ?required=${this.required}>
            <label class="pf-c-switch">
                <input class="pf-c-switch__input" type="checkbox" ?checked=${doCheck} />
                <span class="pf-c-switch__toggle">
                    <span class="pf-c-switch__toggle-icon">
                        <i class="fas fa-check" aria-hidden="true"></i>
                    </span>
                </span>
                <span class="pf-c-switch__label">${this.label}</span>
            </label>
            ${this.help.trim() ? html`<p class="pf-c-form__helper-text">${this.help}</p>` : nothing}
        </ak-form-element-horizontal>`;
    }
}

export default AkSwitchInput;
