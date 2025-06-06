import { ifNotEmpty } from "@goauthentik/elements/utils/ifNotEmpty.js";

import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { AkPrivateTextInput } from "./ak-private-text-input.js";

@customElement("ak-private-textarea-input")
export class AkPrivateTextAreaInput extends AkPrivateTextInput {
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
            placeholder=${ifNotEmpty(this.placeholder)}
            autocomplete=${ifDefined(code ? "off" : undefined)}
            spellcheck=${ifDefined(code ? "false" : undefined)}
        >${this.value !== undefined ? this.value : ""}</textarea
        > `;
    }
}

export default AkPrivateTextAreaInput;

declare global {
    interface HTMLElementTagNameMap {
        "ak-private-textarea-input": AkPrivateTextAreaInput;
    }
}
