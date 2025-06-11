import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { HorizontalLightComponent } from "./HorizontalLightComponent";

@customElement("ak-number-input")
export class AkNumberInput extends HorizontalLightComponent<number> {
    @property({ type: Number, reflect: true })
    value = NaN;

    @property({ type: Number, reflect: true })
    min = NaN;

    renderControl() {
        const setValue = (ev: InputEvent) => {
            const value = (ev.target as HTMLInputElement).value;
            this.value = value.trim() === "" ? NaN : parseInt(value, 10);
        };

        return html`<input
            type="number"
            @input=${setValue}
            aria-label=${ifDefined(this.label)}
            value=${ifDefined(this.value)}
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
