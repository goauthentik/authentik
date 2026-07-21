/**
 * @file * @file Document-level CSS Custom Properties for Label components.
 */

import Styles from "./Label.styles";

import { classList } from "#elements/directives/class-list";
import FAIcons from "#elements/Icons_impl/Icons.styles";
import type { SlottedTemplateResult, Spread } from "#elements/types";

import { spread } from "@open-wc/lit-helpers";

import { html, LitElement, nothing } from "lit";
import { property, state } from "lit/decorators.js";

const labelColors = ["blue", "green", "orange", "red", "purple", "cyan", "gold", "gray"] as const;
export type LabelColor = (typeof labelColors)[number];

export const statusNames = [
    "info",
    "success",
    "warning",
    "danger",
    "running",
    "neutral",
    "good",
    "bad",
    "ok",
];
export type Status = (typeof statusNames)[number];

type StatusDetail = [LabelColor, string];
// prettier-ignore
const chromeList: Map<Status, StatusDetail> = new Map([
    ["danger",  ["red", "fa-times"]],
    ["error",   ["red", "fa-times"]],
    ["warning", ["orange", "fa-exclamation-triangle"]],
    ["bad",     ["orange", "fa-exclamation-triangle"]],
    ["success", ["green", "fa-check"]],
    ["good",    ["green", "fa-check"]],
    ["ok",      ["green", "fa-check"]],
    ["running", ["blue", "fa-clock"]],
    ["info",    ["gray", "fa-info-circle"]],
    ["neutral", ["gray", "fa-times"]],
    ["unknown", ["gray", "fa-question"]],
]);

export class Label extends LitElement {
    static readonly styles = [Styles, FAIcons];

    // Setting `status` will override setting `color`
    @property()
    status?: Status;

    @property()
    icon?: string;

    // This is *deliberately* not included in the slot lifecycle.  It is here
    // for child classes to provide their own labeling scheme.
    @state()
    label?: string;

    @state()
    protected hasSlottedIcon = false;

    private handleIconSlotChange = (ev: Event) => {
        const nodes = (ev.target as HTMLSlotElement).assignedNodes({ flatten: false });
        this.hasSlottedIcon = nodes.some(
            (n) =>
                n.nodeType === Node.ELEMENT_NODE ||
                (n.nodeType === Node.TEXT_NODE && (n.textContent ?? "").trim().length > 0)
        );
    };

    get statusDetails(): StatusDetail | [null, null] {
        const status = this.status ? chromeList.get(this.status) : null;
        if (this.status && !status) {
            console.warn(
                `${this.tagName.toLowerCase()}: '${this.status}' is not a valid status token.`
            );
        }
        return status ? status : [null, null];
    }

    get isIconPresent() {
        return Boolean(this.icon || this.status || this.hasSlottedIcon);
    }

    getIcon() {
        const [_, iconClass] = this.statusDetails;
        const icon = this.icon ?? iconClass;
        return icon ? html`<i class="fas fa-fw ${icon}" aria-hidden="true"></i>` : nothing;
    }

    getColor() {
        const [colorName, _] = this.statusDetails;
        return colorName ? `status-${colorName}` : null;
    }

    render() {
        const iconClass = classList([this.isIconPresent && "has-content"]);
        const colorClass = classList([this.getColor()]);

        return html` <span part="label" class="${colorClass}">
            <span part="icon" class=${iconClass}
                ><slot name="icon" @slotchange=${this.handleIconSlotChange}
                    >${this.getIcon()}</slot
                ></span
            >
            <span part="text">${this.label ? this.label : html`<slot></slot>`}</span>
        </span>`;
    }
}

export interface LabelProps {
    icon?: string;
    color?: string;
    compact?: boolean;
    outline?: boolean;
    status?: Status;
}

export function akLabel(properties: LabelProps, content: SlottedTemplateResult = nothing) {
    const message = typeof content === "string" ? html`<span>${content}</span>` : content;
    return html`<ak-label ${spread(properties as Spread)}>${message}</ak-label>`;
}
