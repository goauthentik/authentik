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

    @property({ type: Number, attribute: "maxlength" })
    public maxLength?: number;

    @property({ type: Number, attribute: "minlength" })
    public minLength?: number;

    @property({ type: Boolean, attribute: "readonly" })
    public readOnly: boolean = false;

    @property({ type: String, attribute: "inputmode", useDefault: true })
    inputMode: string = "text";

    @property({ type: String })
    public type: "text" | "email" = "text";

    #inputListener(ev: InputEvent) {
        this.value = (ev.target as HTMLInputElement).value;
    }

    public override renderControl() {
        const code = this.inputHint === "code";

        return html`<input
            type=${this.type}
            id=${ifDefined(this.fieldID)}
            @input=${this.#inputListener}
            value=${ifDefined(this.value)}
            class="${classMap({
                "pf-c-form-control": true,
                "pf-m-monospace": code,
            })}"
            maxlength=${ifPresent(this.maxLength)}
            minlength=${ifPresent(this.minLength)}
            autocomplete=${ifPresent(code ? "off" : this.autocomplete)}
            spellcheck=${ifPresent(code ? "false" : this.spellcheck)}
            aria-describedby=${this.helpID}
            placeholder=${ifPresent(this.placeholder)}
            inputmode=${this.inputMode}
            ?required=${this.required}
            ?autofocus=${this.autofocus}
            ${this.autofocusTarget.toRef()}
        />`;
    }
}

export default AkTextInput;

declare global {
    interface HTMLElementTagNameMap {
        "ak-text-input": AkTextInput;
    }
}
