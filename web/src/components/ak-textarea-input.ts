import { HorizontalLightComponent } from "./HorizontalLightComponent.js";

import { ifPresent } from "#elements/utils/attributes";

import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-textarea-input")
export class AkTextareaInput extends HorizontalLightComponent<string> {
    @property({ type: String, reflect: true })
    public value = "";

    @property({ type: String })
    public placeholder: string | null = null;

    public override renderControl() {
        const code = this.inputHint === "code";
        const setValue = (ev: InputEvent) => {
            this.value = (ev.target as HTMLInputElement).value;
        };
        // Prevent the leading spaces added by Prettier's whitespace algo
        // prettier-ignore
        return html`<textarea
            id=${ifDefined(this.fieldID)}
            @input=${setValue}
            class="pf-c-form-control"
            ?required=${this.required}
            name=${this.name}
            placeholder=${ifPresent(this.placeholder)}
            autocomplete=${ifPresent(code, "off")}
            spellcheck=${ifPresent(code, "false")}
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
