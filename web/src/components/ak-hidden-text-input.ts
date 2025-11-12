import "./ak-visibility-toggle.js";

import type { VisibilityToggleProps } from "./ak-visibility-toggle.js";
import {
    HorizontalLightComponent,
    HorizontalLightComponentProps,
} from "./HorizontalLightComponent.js";

import { ifPresent } from "#elements/utils/attributes";

import { msg } from "@lit/localize";
import { css, html } from "lit";
import { customElement, property, query } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

type BaseProps = HorizontalLightComponentProps<string> &
    Pick<VisibilityToggleProps, "showMessage" | "hideMessage">;

export interface AkHiddenTextInputProps extends BaseProps {
    revealed: boolean;
    placeholder: string | null;
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
    public placeholder: string | null = null;

    /**
     * Specify kind of help the browser should try to provide
     *
     * @property
     * @attribute
     */
    @property({ type: String })
    public autocomplete?: AutoFill;

    @property({ type: Boolean, attribute: "readonly" })
    public readOnly: boolean = false;

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

    // TODO: Because of the peculiarities of how HorizontalLightComponent works, keeping its content
    // in the LightDom so the inner components actually inherit styling, the normal `css` options
    // aren't available. Embedding styles is bad styling, and we'll fix it in the next style
    // refresh.
    protected renderInputField(setValue: InputListener, code: boolean) {
        return html` <input
            part="input"
            autocomplete=${ifPresent(this.autocomplete)}
            type=${this.revealed ? "text" : "password"}
            aria-label=${ifPresent(this.label)}
            @input=${setValue}
            value=${ifPresent(this.value)}
            placeholder=${ifPresent(this.placeholder)}
            class="${classMap({
                "pf-c-form-control": true,
                "pf-m-monospace": code,
            })}"
            spellcheck=${code ? "false" : "true"}
            id=${ifPresent(this.fieldID)}
            aria-describedby=${this.helpID}
            ?required=${this.required}
            ?readonly=${this.readOnly}
        />`;
    }

    protected override renderControl() {
        const code = this.inputHint === "code";
        const setValue: InputListener = (ev) => {
            this.value = (ev.target as T).value;
        };

        return html`<div style="display: flex;" part="control">
            ${this.renderInputField(setValue, code)}
            <ak-visibility-toggle
                part="toggle"
                style="flex: 0 0 auto; align-self: flex-start"
                ?open=${this.revealed}
                show-message=${this.showMessage}
                hide-message=${this.hideMessage}
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
