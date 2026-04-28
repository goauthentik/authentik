import { HorizontalLightComponent } from "./HorizontalLightComponent.js";

import { ifPresent } from "#elements/utils/attributes";

import { msg } from "@lit/localize";
import { html, PropertyValues } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { createRef, ref } from "lit/directives/ref.js";
import { styleMap } from "lit/directives/style-map.js";

@customElement("ak-secret-text-input")
export class AkSecretTextInput extends HorizontalLightComponent<string> {
    @property({ type: String })
    public value = "";

    @property({ type: Boolean, reflect: true })
    public revealed = false;

    @property({ type: String })
    public placeholder = "";

    @property({ type: Number, attribute: "maxlength" })
    public maxLength?: number;

    @property({ type: Number, attribute: "minlength" })
    public minLength?: number;

    public reveal = () => {
        this.revealed = true;
    };

    #inputListener = (ev: InputEvent) => {
        this.value = (ev.target as HTMLInputElement).value;
    };

    #ref = createRef<HTMLInputElement>();

    public override updated(changedProperties: PropertyValues<this>): void {
        super.updated(changedProperties);

        if (changedProperties.has("revealed") && this.revealed) {
            this.#ref.value?.focus();
        }
    }

    #renderSecretInput() {
        return html`<div
            class="pf-c-form__horizontal-group"
            style=${styleMap({
                display: "flex",
                gap: "var(--pf-global--spacer--sm)",
            })}
        >
            <input
                @click=${this.reveal}
                id=${this.fieldID}
                aria-describedby=${this.helpID}
                class="pf-c-form-control"
                type="password"
                disabled
                data-form-ignore="true"
                value="**************"
            />
            <input
                type="text"
                value="${ifDefined(this.value)}"
                ?required=${this.required}
                name=${ifDefined(this.name)}
                hidden
            />
            <button
                id=${this.helpID}
                class="pf-c-button pf-m-tertiary pf-m-inline"
                type="button"
                @click=${this.reveal}
            >
                ${msg("Modify", {
                    id: "ak-secret-text-input.actions.modify",
                    desc: "Help text for secret input field to indicate that clicking will allow changing the value.",
                })}
            </button>
        </div>`;
    }

    protected renderVisibleInput() {
        const code = this.inputHint === "code";
        const classes = {
            "pf-c-form-control": true,
            "pf-m-monospace": code,
        };

        return html`<input
            ${ref(this.#ref)}
            type="text"
            id=${this.fieldID}
            aria-describedby=${this.helpID}
            @input=${this.#inputListener}
            name=${ifDefined(this.name)}
            value=${ifDefined(this.value)}
            class="${classMap(classes)}"
            maxlength=${ifPresent(this.maxLength)}
            minlength=${ifPresent(this.minLength)}
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
