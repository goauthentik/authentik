import { AkHiddenTextInput, type AkHiddenTextInputProps } from "./ak-hidden-text-input.js";

import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
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
    //#region Properties

    /**
     * Number of visible text lines (rows)
     *
     * @property
     * @attribute
     */
    @property({ type: Number })
    public rows?: number = 4;

    /**
     * Nummber of visible character width (cols)
     * @property
     * @attribute
     */
    @property({ type: Number })
    public cols?: number;

    /**
     * You want `resize=true` so that the resize value is visible in the component tag, activating the CSS associated with these values.
     *
     * @property
     * @attribute
     */
    @property({ type: String, reflect: true })
    public resize?: "none" | "both" | "horizontal" | "vertical" = "vertical";

    /**
     * @property
     * @attribute
     */
    @property({ type: String })
    public wrap?: "soft" | "hard" | "off" = "soft";

    //#endregion

    get #visibleValue() {
        const value = this.value ?? "";
        if (this.revealed) {
            return value;
        }

        return value
            .split("\n")
            .reduce((acc: string[], line: string) => [...acc, "*".repeat(line.length)], [])
            .join("\n");
    }

    //#region Rendering

    protected override renderInputField() {
        const wrap = this.revealed ? this.wrap : "soft";
        const code = this.inputHint === "code";

        return html`
            <textarea
                style="flex: 1 1 auto; min-width: 0;"
                part="textarea"
                @input=${this}
                id=${ifDefined(this.fieldID)}
                placeholder=${ifDefined(this.placeholder)}
                aria-label=${ifDefined(this.label)}
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
${this.#visibleValue}</textarea
            >
        `;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-hidden-textarea-input": AkHiddenTextAreaInput;
    }
}
