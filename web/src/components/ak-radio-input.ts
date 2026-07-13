import "#elements/forms/Radio";

import { HorizontalLightComponent } from "./HorizontalLightComponent.js";

import { RadioChangeEventDetail, RadioOption } from "#elements/forms/Radio";
import { SlottedTemplateResult } from "#elements/types";

import type { Jsonifiable } from "type-fest";

import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-radio-input")
export class AkRadioInput<T extends Jsonifiable> extends HorizontalLightComponent<T> {
    public override role = "radiogroup";

    @property({ type: Object })
    public value!: T;

    @property({ attribute: false })
    public options: RadioOption<T>[] | (() => RadioOption<T>[]) = [];

    handleInput(ev: CustomEvent<RadioChangeEventDetail<T>>): void {
        if ("detail" in ev) {
            this.value = ev.detail.value;
        }
    }

    protected override renderHelp(): SlottedTemplateResult {
        return nothing;
    }

    protected override renderControl(): SlottedTemplateResult {
        const helpText = this.help?.trim();

        return html`${helpText
                ? html`<p part="radio-help" class="pf-c-form__helper-radio" id=${this.helpID}>
                      ${helpText}
                  </p>`
                : null}<ak-radio
                .options=${this.options}
                .value=${this.value}
                @input=${this.handleInput}
                aria-describedby=${this.help ? this.helpID : nothing}
                part="radio"
            >
            </ak-radio>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-radio-input": AkRadioInput<Jsonifiable>;
    }
}

export default AkRadioInput;
