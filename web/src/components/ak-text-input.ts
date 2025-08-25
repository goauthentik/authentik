import { HorizontalLightComponent } from "./HorizontalLightComponent.js";

import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-text-input")
export class AkTextInput extends HorizontalLightComponent<string> {
    @property({ type: String, reflect: true })
    public value = "";

    @property({ type: String })
    public autocomplete?: AutoFill;

    @property({ type: String })
    public placeholder?: string;

    #inputListener(ev: InputEvent) {
        this.value = (ev.target as HTMLInputElement).value;
    }

    public override renderControl() {
        const code = this.inputHint === "code";

        return html` <input
            type="text"
            role="textbox"
            id=${ifDefined(this.fieldID)}
            @input=${this.#inputListener}
            value=${ifDefined(this.value)}
            class="${classMap({
                "pf-c-form-control": true,
                "pf-m-monospace": code,
            })}"
            autocomplete=${ifDefined(code ? "off" : this.autocomplete)}
            spellcheck=${ifDefined(code ? "false" : undefined)}
            aria-label=${ifDefined(this.placeholder || this.label)}
            placeholder=${ifDefined(this.placeholder)}
            ?required=${this.required}
        />`;
    }
}

export default AkTextInput;

declare global {
    interface HTMLElementTagNameMap {
        "ak-text-input": AkTextInput;
    }
}
