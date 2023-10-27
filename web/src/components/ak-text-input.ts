import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { HorizontalLightComponent } from "./HorizontalLightComponent";

@customElement("ak-text-input")
export class AkTextInput extends HorizontalLightComponent {
    @property({ type: String, reflect: true })
    value = "";

    renderControl() {
        return html` <input
            type="text"
            value=${ifDefined(this.value)}
            class="pf-c-form-control"
            ?required=${this.required}
        />`;
    }
}

export default AkTextInput;
