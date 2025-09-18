import { HorizontalLightComponent } from "./HorizontalLightComponent.js";

import { ifPresent } from "#elements/utils/attributes";

import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-text-input")
export class AkTextInput extends HorizontalLightComponent<string> {
    @property({ type: String, reflect: true })
    public value = "";

    @property({ type: String })
    public autocomplete: AutoFill | null = null;

    @property({ type: String })
    public placeholder: string | null = null;

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
            autocomplete=${ifPresent(code ? "off" : this.autocomplete)}
            spellcheck=${ifPresent(code ? "false" : this.spellcheck)}
            aria-label=${ifPresent(this.placeholder || this.label)}
            aria-describedby=${this.helpID}
            placeholder=${ifPresent(this.placeholder)}
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
