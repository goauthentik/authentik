import { AkSecretTextInput } from "./ak-secret-text-input.js";

import { ifPresent } from "#elements/utils/attributes";

import { html } from "lit";
import { customElement } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { ref } from "lit/directives/ref.js";

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

        return html`<textarea
            ${ref(this.inputRef)}
            id=${this.fieldID}
            aria-describedby=${this.helpID}
            rows="4"
            .value=${this.value}
            @input=${setValue}
            class="${classMap(classes)}"
            ?required=${this.required}
            name=${this.name}
            placeholder=${ifPresent(this.placeholder)}
            autocomplete=${ifDefined(code ? "off" : undefined)}
            spellcheck=${ifDefined(code ? "false" : undefined)}
        ></textarea>`;
    }
}

export default AkSecretTextAreaInput;

declare global {
    interface HTMLElementTagNameMap {
        "ak-secret-textarea-input": AkSecretTextAreaInput;
    }
}
