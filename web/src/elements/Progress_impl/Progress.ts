import styles from "./Progress.styles";

import type { ElementRest } from "#elements/types";

import { spread } from "@open-wc/lit-helpers";

import { html, LitElement, nothing, TemplateResult } from "lit";
import { property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { styleMap } from "lit/directives/style-map.js";

export const progressVariants = ["none", "top", "inside", "outside", "indeterminate"] as const;
export type ProgressVariant = (typeof progressVariants)[number];

export const progressSize = ["xs", "sm", "md", "lg"] as const;
export type ProgressSize = (typeof progressSize)[number];

export const progressSeverity = ["success", "danger", "warning"] as const;
export type ProgressSeverity = (typeof progressSeverity)[number];

/**
 * @element ak-progress
 *
 * @summary A progress bar component that displays the completion progress of a task with
 * customizable variants and severity states
 *
 * @attr {string} variant - Display variant: "none", "top", "inside", "outside"
 * @attr {string} size - Size variant: "sm", "lg"
 * @attr {string} severity - Severity state: "success", "danger", "warning"
 * @attr {number} min - Minimum value for progress range
 * @attr {number} max - Maximum value for progress range
 * @attr {number} value - Current progress value
 * @attr {boolean} one-way - Prevents progress value from decreasing
 *
 * @slot label - Label text (renders in grid row 1, spans columns 1-2 for outside variant)
 *
 * @remarks
 * The component uses CSS Grid with specific positioning. Do not override override grid-column or
 * grid-row properties in your slotted content as this will break the layout contract defined by
 * PatternFly 5.
 *
 * @csspart main - The main container element
 * @csspart status - Container for progress value
 * @csspart bar - The background progress bar container
 * @csspart indicator - The filled portion of the progress bar
 * @csspart measure - Text display of the current progress value
 * @csspart label - Container for the label text
 *
 */
export class Progress extends LitElement {
    static readonly styles = [styles];

    @property({ type: String, reflect: true })
    public variant: ProgressVariant = "top";

    @property({ reflect: true })
    public severity?: ProgressSeverity;

    @property({ type: Number })
    public min = 0;

    @property({ type: Number })
    public max = 100;

    private _value = 0;

    @property({ type: Number })
    set value(value: number) {
        if (this.oneWay && value < this._value) {
            return;
        }
        this._value = value;
    }

    public get value() {
        return this._value;
    }

    public reset() {
        this._value = this.min;
        this.requestUpdate();
    }

    @property({ type: Boolean, attribute: "one-way" })
    public oneWay = false;

    @property({ type: Object })
    public displayValue = (value: number) => `${value}%`;

    protected get renderedValue() {
        return this.displayValue(this.value);
    }

    protected getSlotted(name: string) {
        const selector = `[slot="${name}"]`;
        return Array.from(this.children).find((e) => e.matches(selector));
    }

    protected get percentage() {
        if (this.max <= this.min) {
            return this.value >= this.max ? 100 : 0;
        }

        const range = this.max - this.min;
        const normalized = Math.min(Math.max(this.value, this.min), this.max);
        return ((normalized - this.min) / range) * 100;
    }

    public override render() {
        const width = {
            width: this.variant === "indeterminate" ? undefined : `${this.percentage}%`,
        };

        const showStatus = this.variant !== "none";

        const label = this.getSlotted("label")
            ? html`<div part="label" aria-hidden="true"><slot name="label"></slot></div>`
            : nothing;

        const measure =
            showStatus && (this.variant === "top" || this.variant === "outside")
                ? html`<span class="measure">${this.renderedValue}</span>`
                : nothing;

        const status = showStatus ? html`<div part="status">${measure}</div>` : nothing;

        return html` <div part="main">
            ${label}
            <!-- -->
            ${status}
            <div part="bar">
                <div part="indicator" style=${styleMap(width)}>
                    ${this.variant === "inside"
                        ? html`<span part="measure">${this.renderedValue}</span>`
                        : nothing}
                </div>
            </div>
        </div>`;
    }
}

export type ProgressProps = ElementRest &
    Partial<
        Pick<Progress, "variant" | "severity" | "min" | "max" | "value" | "oneWay" | "displayValue">
    > & {
        size?: ProgressSize;
        label?: string | TemplateResult;
    };

/**
 * @summary Helper function to create a Progress component programmatically
 *
 * @returns {TemplateResult} A Lit template result containing the configured ak-progress element
 *
 * @see {@link Progress} - The underlying web component
 */
export function akProgress(options: ProgressProps) {
    const { variant, size, severity, min, max, value, oneWay, displayValue, label, ...rest } =
        options;

    return html`
        <ak-progress
            ${spread(rest)}
            variant=${ifDefined(variant)}
            size=${ifDefined(size)}
            severity=${ifDefined(severity)}
            ?one-way=${oneWay}
            min=${ifDefined(min)}
            max=${ifDefined(max)}
            value=${ifDefined(value)}
            .displayValue=${displayValue}
        >
            ${label ? html`<div slot="label">${label}</div>` : nothing}
        </ak-progress>
    `;
}
