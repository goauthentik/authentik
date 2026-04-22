import { HorizontalLightComponent } from "./HorizontalLightComponent.js";

import { ifPresent } from "#elements/utils/attributes";

import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-textarea-input")
export class AkTextareaInput extends HorizontalLightComponent<string> {
    @property({ type: String, reflect: true })
    public value = "";

    @property({ type: Number })
    public rows?: number;

    @property({ type: Number })
    public maxLength: number = -1;

    @property({ type: String })
    public placeholder: string = "";

    public override connectedCallback(): void {
        super.connectedCallback();
        // Listen for form reset events to clear the value
        this.closest("form")?.addEventListener("reset", this.handleReset);
    }

    disconnectedCallback(): void {
        super.disconnectedCallback();
        this.closest("form")?.removeEventListener("reset", this.handleReset);
    }

    private handleReset = (): void => {
        this.value = "";
    };

    public override renderControl() {
        const code = this.inputHint === "code";
        const setValue = (ev: InputEvent) => {
            this.value = (ev.target as HTMLInputElement).value;
        };
        // Prevent the leading spaces added by Prettier's whitespace algo
        // prettier-ignore
        return html`<textarea
            id=${ifPresent(this.fieldID)}
            @input=${setValue}
            class="pf-c-form-control"
            ?required=${this.required}
            name=${this.name}
            rows=${ifPresent(this.rows)}
            maxlength=${(this.maxLength >= 0) ? this.maxLength : nothing}
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
