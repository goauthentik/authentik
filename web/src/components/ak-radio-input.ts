import "#elements/forms/Radio";

import { HorizontalLightComponent } from "./HorizontalLightComponent.js";

import { RadioOption } from "#elements/forms/Radio";
import { SlottedTemplateResult } from "#elements/types";

import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-radio-input")
export class AkRadioInput<T> extends HorizontalLightComponent<T> {
    @property({ type: Object })
    value!: T;

    @property({ type: Array })
    options: RadioOption<T>[] = [];

    handleInput(ev: CustomEvent) {
        if ("detail" in ev) {
            this.value = ev.detail.value;
        }
    }

    protected override renderHelp(): SlottedTemplateResult {
        return nothing;
    }

    renderControl() {
        const helpText = this.help.trim();

        return html`<ak-radio
                label=${ifDefined(this.label)}
                .options=${this.options}
                .value=${this.value}
                @input=${this.handleInput}
            ></ak-radio>
            ${helpText ? html`<p class="pf-c-form__helper-radio">${helpText}</p>` : nothing}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-radio-input": AkRadioInput<unknown>;
    }
}

export default AkRadioInput;
