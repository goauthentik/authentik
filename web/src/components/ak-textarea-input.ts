import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { HorizontalLightComponent } from "./HorizontalLightComponent";

@customElement("ak-textarea-input")
export class AkTextareaInput extends HorizontalLightComponent<string> {
    @property({ type: String, reflect: true })
    value = "";

    renderControl() {
        // Prevent the leading spaces added by Prettier's whitespace algo
        // prettier-ignore
        return html`<textarea
            class="pf-c-form-control"
            ?required=${this.required}
            name=${this.name}
        >${this.value !== undefined ? this.value : ""}</textarea
        > `;
    }
}

export default AkTextareaInput;

declare global {
    interface HTMLElementTagNameMap {
        "ak-textarea-input": AkTextareaInput;
    }
}
