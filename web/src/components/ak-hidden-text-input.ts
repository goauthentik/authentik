import "./ak-visibility-toggle.js";

import type { VisibilityToggleProps } from "./ak-visibility-toggle.js";
import {
    HorizontalLightComponent,
    HorizontalLightComponentProps,
} from "./HorizontalLightComponent.js";

import { msg } from "@lit/localize";
import { css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { ifDefined } from "lit/directives/if-defined.js";

type BaseProps = HorizontalLightComponentProps<string> &
    Pick<VisibilityToggleProps, "hideContentLabel" | "revealContentLabel">;

export interface AkHiddenTextInputProps extends BaseProps {
    revealed: boolean;
    placeholder?: string;
}

export type InputLike = HTMLTextAreaElement | HTMLInputElement;

export type InputListener = (ev: InputEvent) => void;

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
    public static styles = [
        css`
            main {
                display: flex;
            }
        `,
    ];

    /**
     * @property
     * @attribute
     */

    @property({ type: String, reflect: true })
    public value = "";

    /**
     * Whether the input value is visible.
     *
     * @property
     * @attribute
     */
    @property({ type: Boolean, reflect: true })
    public revealed = false;

    /**
     * Placeholder text when no value is set.
     *
     * @property
     * @attribute
     */
    @property({ type: String })
    public placeholder?: string;

    /**
     * Specify kind of help the browser should try to provide.
     *
     * @property
     * @attribute
     */
    @property({ type: String })
    public autocomplete?: AutoFill;

    /**
     * @property
     * @attribute
     */
    @property({ type: String, attribute: "show-message" })
    public revealContentLabel = msg("Show field content");

    /**
     * @property
     * @attribute
     */
    @property({ type: String, attribute: "hide-message" })
    public hideContentLabel = msg("Hide field content");

    /**
     * A listener for the input event.
     */
    protected inputListener = (event: InputEvent) => {
        this.value = (event.target as T).value;
    };

    /**
     * Render the input field.
     *
     * TODO: Because of the peculiarities of how HorizontalLightComponent works, keeping its content LightDOM so the inner components actually inherit styling, the normal `css` options aren't available. Embedding styles is bad styling, and we'll fix it in the next style refresh.
     */
    protected renderInputField() {
        const code = this.inputHint === "code";

        return html` <input
            part="input"
            id=${ifDefined(this.fieldID)}
            autocomplete=${ifDefined(this.autocomplete)}
            type=${this.revealed ? "text" : "password"}
            aria-label=${ifDefined(this.label)}
            @input=${this.inputListener}
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
        return html` <div style="display: flex; gap: 0.25rem">
            ${this.renderInputField()}
            <ak-visibility-toggle
                part="toggle"
                style="flex: 0 0 auto; align-self: flex-start"
                ?open=${this.revealed}
                show-message=${this.revealContentLabel}
                hide-message=${this.hideContentLabel}
                @click=${() => (this.revealed = !this.revealed)}
            ></ak-visibility-toggle>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-hidden-text-input": AkHiddenTextInput;
    }
}
