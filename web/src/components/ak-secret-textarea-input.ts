import { AkSecretTextInput } from "./ak-secret-text-input.js";

import { ifPresent } from "#elements/utils/attributes";

import { html } from "lit";
import { customElement } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-secret-textarea-input")
export class AkSecretTextAreaInput extends AkSecretTextInput {
    protected override renderVisibleInput() {
        const code = this.inputHint === "code";
        const setValue = (ev: InputEvent) => {
            this.value = (ev.target as HTMLInputElement).value;
        };
        const classes = {
            "pf-c-form-control": true,
            "pf-m-monospace": code,
        };

        // Prevent the leading spaces added by Prettier's whitespace algo
        // prettier-ignore
        return html`<textarea
            @input=${setValue}
            class="${classMap(classes)}"
            ?required=${this.required}
            name=${this.name}
            placeholder=${ifPresent(this.placeholder)}
            autocomplete=${ifDefined(code ? "off" : undefined)}
            spellcheck=${ifDefined(code ? "false" : undefined)}
        >${this.value !== undefined ? this.value : ""}</textarea
        > `;
    }
}

export default AkSecretTextAreaInput;

declare global {
    interface HTMLElementTagNameMap {
        "ak-secret-textarea-input": AkSecretTextAreaInput;
    }
}
