import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { HorizontalLightComponent } from "./HorizontalLightComponent";

@customElement("ak-number-input")
export class AkNumberInput extends HorizontalLightComponent {
    @property({ type: Number, reflect: true })
    value = 0;

    renderControl() {
        return html`<input
                type="number"
                value=${ifDefined(this.value)}
                class="pf-c-form-control"
                ?required=${this.required}
            />`;
    }
}

export default AkNumberInput;
