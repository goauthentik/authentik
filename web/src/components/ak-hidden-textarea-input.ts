import {
    AkHiddenTextInput,
    type AkHiddenTextInputProps,
    InputListener,
} from "./ak-hidden-text-input.js";

import { ifPresent } from "#elements/utils/attributes";

import { html } from "lit";
import { customElement, property, query } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { ifDefined } from "lit/directives/if-defined.js";

export interface AkHiddenTextAreaInputProps extends AkHiddenTextInputProps {
    /**
     * Number of visible text lines (rows)
     */
    rows?: number;

    /**
     * Number of visible character width (cols)
     */
    cols?: number;

    /**
     * How the textarea can be resized
     */
    resize?: "none" | "both" | "horizontal" | "vertical";

    /**
     * Whether text should wrap
     */
    wrap?: "soft" | "hard" | "off";
}

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
@customElement("ak-hidden-textarea-input")
export class AkHiddenTextAreaInput
    extends AkHiddenTextInput<HTMLTextAreaElement>
    implements AkHiddenTextAreaInputProps
{
    /* These are mostly just forwarded to the textarea component. */

    /**
     * @property
     * @attribute
     */
    @property({ type: Number })
    rows?: number = 4;

    /**
     * @property
     * @attribute
     */
    @property({ type: Number })
    cols?: number;

    /**
     * @property
     * @attribute
     *
     * You want `resize=true` so that the resize value is visible in the component tag, activating
     * the CSS associated with these values.
     */
    @property({ type: String, reflect: true })
    resize?: "none" | "both" | "horizontal" | "vertical" = "vertical";

    /**
     * @property
     * @attribute
     */
    @property({ type: String })
    wrap?: "soft" | "hard" | "off" = "soft";

    @query("#main > textarea")
    protected inputField!: HTMLTextAreaElement;

    get displayValue() {
        const value = this.value ?? "";
        if (this.revealed) {
            return value;
        }

        return value
            .split("\n")
            .reduce((acc: string[], line: string) => [...acc, "*".repeat(line.length)], [])
            .join("\n");
    }

    // TODO: Because of the peculiarities of how HorizontalLightComponent works, keeping its content
    // in the LightDom so the inner components actually inherit styling, the normal `css` options
    // aren't available. Embedding styles is bad styling, and we'll fix it in the next style
    // refresh.
    protected override renderInputField(setValue: InputListener, code: boolean) {
        const wrap = this.revealed ? this.wrap : "soft";

        return html`
            <textarea
                style="flex: 1 1 auto; min-width: 0;"
                part="textarea"
                @input=${setValue}
                placeholder=${ifPresent(this.placeholder)}
                aria-label=${ifPresent(this.label)}
                rows=${ifDefined(this.rows)}
                cols=${ifDefined(this.cols)}
                wrap=${ifDefined(wrap)}
                class=${classMap({
                    "pf-c-form-control": true,
                    "pf-m-monospace": code,
                })}
                spellcheck=${code ? "false" : "true"}
                ?required=${this.required}
            >
${this.displayValue}</textarea
            >
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-hidden-textarea-input": AkHiddenTextAreaInput;
    }
}
