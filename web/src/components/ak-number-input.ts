import { HorizontalLightComponent } from "./HorizontalLightComponent.js";

import { ifPresent } from "#elements/utils/attributes";

import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-number-input")
export class AkNumberInput extends HorizontalLightComponent<number> {
    @property({ type: Number, reflect: true })
    value = NaN;

    @property({ type: Number, reflect: true })
    min = NaN;

    @property({ type: Boolean, reflect: true })
    allowFloat = false;

    renderControl() {
        const setValue = (ev: InputEvent) => {
            const value = (ev.target as HTMLInputElement).value.trim();

            if (value === "") {
                this.value = NaN;
                return;
            }

            this.value = this.allowFloat === true ? parseFloat(value) : parseInt(value, 10);
        };

        return html`<input
            id=${this.fieldID}
            aria-describedby=${this.helpID}
            type="number"
            @input=${setValue}
            aria-label=${ifPresent(this.label)}
            value=${ifPresent(this.value)}
            min=${ifDefined(this.min)}
            class="pf-c-form-control"
            ?required=${this.required}
        />`;
    }
}

export default AkNumberInput;

declare global {
    interface HTMLElementTagNameMap {
        "ak-number-input": AkNumberInput;
    }
}
