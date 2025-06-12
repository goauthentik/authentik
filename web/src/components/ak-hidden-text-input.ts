import { bound } from "#elements/decorators/bound";

import { msg } from "@lit/localize";
import { css, html } from "lit";
import { customElement, property, query } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    HorizontalLightComponent,
    HorizontalLightComponentProps,
} from "./HorizontalLightComponent";
import "./ak-visibility-toggle.js";
import type { VisibilityToggleProps } from "./ak-visibility-toggle.js";

type BaseProps = HorizontalLightComponentProps<string> &
    Pick<VisibilityToggleProps, "showMessage" | "hideMessage">;

export interface AkHiddenTextInputProps extends BaseProps {
    revealed: boolean;
    placeholder?: string;
}

export type InputLike = HTMLTextAreaElement | HTMLInputElement;

/**
 * @element ak-hidden-text-input
 * @class AkHiddenTextInput
 *
 * A text-input field with a visibility control, so you can show/hide sensitive fields.
 *
 * ## CSS Parts
 * @csspart container - The main container div
 * @csspart input - The input element
 * @csspart toggle - The visibility toggle button
 *
 */
@customElement("ak-hidden-text-input")
export class AkHiddenTextInput<T extends InputLike = HTMLInputElement>
    extends HorizontalLightComponent<string>
    implements AkHiddenTextInputProps
{
    static get styles() {
        return [
            css`
                :host {
                    --ak-hidden-text-input-gap: var(--pf-v5-global--spacer--xs, 0.25rem);
                }
                #main {
                    display: flex;
                    width: 100%;
                    gap: var(--ak-hidden-text-input-gap);
                }
                #main > input {
                    flex: 1 1 auto;
                    min-width: 0; /* Prevents flex item overflow */
                }
                #main > ak-visibility-toggle {
                    flex: 0 0 auto;
                    align-self: center;
                }
            `,
        ];
    }

    /**
     * @property
     * @attribute
     */
    @property({ type: String, reflect: true })
    public value = "";

    /**
     * @property
     * @attribute
     */
    @property({ type: Boolean, reflect: true })
    public revealed = false;

    /**
     * Text for when the input has no set value
     *
     * @property
     * @attribute
     */
    @property({ type: String })
    public placeholder?: string;

    /**
     * Specify kind of help the browser should try to provide
     *
     * @property
     * @attribute
     */
    @property({ type: String })
    public autocomplete?: "none" | AutoFill;

    /**
     * @property
     * @attribute
     */
    @property({ type: String, attribute: "show-message" })
    public showMessage = msg("Show field content");

    /**
     * @property
     * @attribute
     */
    @property({ type: String, attribute: "hide-message" })
    public hideMessage = msg("Hide field content");

    @query("#main > input")
    protected inputField!: T;

    @bound
    private handleToggleVisibility() {
        this.revealed = !this.revealed;

        // Maintain focus on input after toggle
        this.updateComplete.then(() => {
            if (this.inputField && document.activeElement === this) {
                this.inputField.focus();
            }
        });
    }

    protected renderInputField(setValue: (ev: InputEvent) => void, code: boolean) {
        return html` <input
            part="input"
            type=${this.revealed ? "text" : "password"}
            @input=${setValue}
            value=${ifDefined(this.value)}
            placeholder=${ifDefined(this.placeholder)}
            class="${classMap({
                "pf-c-form-control": true,
                "pf-m-monospace": code,
            })}"
            spellcheck=${code ? "false" : "true"}
            ?required=${this.required}
        />`;
    }

    protected override renderControl() {
        const code = this.inputHint === "code";
        const setValue = (ev: InputEvent) => {
            this.value = (ev.target as T).value;
        };
        return html` <div id="main" part="main">
            ${this.renderInputField(setValue, code)}
            <!-- -->
            <ak-visibility-toggle
                part="toggle"
                ?open=${this.revealed}
                show-message=${this.showMessage}
                hide-message=${this.hideMessage}
                @click=${() => (this.revealed = !this.revealed)}
            ></ak-visibility-toggle>
        </div>`;
    }
}

export default AkHiddenTextInput;

declare global {
    interface HTMLElementTagNameMap {
        "ak-hidden-text-input": AkHiddenTextInput;
    }
}
