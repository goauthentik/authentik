import { HorizontalLightComponent } from "./HorizontalLightComponent.js";

import { ifPresent } from "#elements/utils/attributes";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-secret-text-input")
export class AkSecretTextInput extends HorizontalLightComponent<string> {
    @property({ type: String, reflect: true })
    public value = "";

    @property({ type: Boolean, reflect: true })
    public revealed = false;

    @property({ type: String })
    public placeholder = "";

    #onReveal() {
        this.revealed = true;
    }

    #renderSecretInput() {
        return html`<div class="pf-c-form__horizontal-group" @click=${() => this.#onReveal()}>
            <input
                class="pf-c-form-control"
                type="password"
                disabled
                data-form-ignore="true"
                value="**************"
            />
            <input type="text" value="${ifDefined(this.value)}" ?required=${this.required} hidden />
            <p class="pf-c-form__helper-text" aria-live="polite">${msg("Click to change value")}</p>
        </div>`;
    }

    protected renderVisibleInput() {
        const code = this.inputHint === "code";
        const setValue = (ev: InputEvent) => {
            this.value = (ev.target as HTMLInputElement).value;
        };
        const classes = {
            "pf-c-form-control": true,
            "pf-m-monospace": code,
        };

        return html` <input
            type="text"
            @input=${setValue}
            value=${ifDefined(this.value)}
            class="${classMap(classes)}"
            placeholder=${ifPresent(this.placeholder)}
            autocomplete=${ifDefined(code ? "off" : undefined)}
            spellcheck=${ifDefined(code ? "false" : undefined)}
            ?required=${this.required}
        />`;
    }

    public override renderControl() {
        return this.revealed ? this.renderVisibleInput() : this.#renderSecretInput();
    }
}

export default AkSecretTextInput;

declare global {
    interface HTMLElementTagNameMap {
        "ak-secret-text-input": AkSecretTextInput;
    }
}
