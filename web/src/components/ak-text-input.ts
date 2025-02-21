import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { HorizontalLightComponent } from "./HorizontalLightComponent";

@customElement("ak-text-input")
export class AkTextInput extends HorizontalLightComponent<string> {
    @property({ type: String, reflect: true })
    value = "";

    renderControl() {
        const setValue = (ev: InputEvent) => {
            this.value = (ev.target as HTMLInputElement).value;
        };

        const code = this.inputHint === "code";

        return html` <input
            type="text"
            @input=${setValue}
            value=${ifDefined(this.value)}
            class="${classMap({
                "pf-c-form-control": true,
                "pf-m-monospace": code,
            })}"
            autocomplete=${ifDefined(code ? "off" : undefined)}
            spellcheck=${ifDefined(code ? "false" : undefined)}
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
