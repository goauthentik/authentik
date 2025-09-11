import { AKElement } from "#elements/Base";
import type { SlottedTemplateResult, Spread } from "#elements/types";

import { spread } from "@open-wc/lit-helpers";

import { css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import PFLabel from "@patternfly/patternfly/components/Label/label.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export enum PFColor {
    Green = "pf-m-green",
    Orange = "pf-m-orange",
    Red = "pf-m-red",
    Blue = "pf-m-blue",
    Grey = "",
}

export const levelNames = ["warning", "info", "success", "danger"];
export type Level = (typeof levelNames)[number];

type Chrome = [Level, PFColor, string, string];
const chromeList: Chrome[] = [
    ["danger", PFColor.Red, "pf-m-red", "fa-times"],
    ["warning", PFColor.Orange, "pf-m-orange", "fa-exclamation-triangle"],
    ["success", PFColor.Green, "pf-m-green", "fa-check"],
    ["running", PFColor.Blue, "pf-m-blue", "fa-clock"],
    ["info", PFColor.Grey, "pf-m-grey", "fa-info-circle"],
];

export interface ILabel {
    icon?: string;
    compact?: boolean;
    color?: string;
}

@customElement("ak-label")
export class Label extends AKElement implements ILabel {
    @property()
    color: PFColor = PFColor.Grey;

    @property()
    icon?: string;

    @property({ type: Boolean })
    compact = false;

    static styles = [
        PFBase,
        PFLabel,
        css`
            :host([theme="dark"]) {
                .pf-m-grey {
                    --pf-c-label__icon--Color: var(--ak-dark-background);
                    --pf-c-label__content--Color: var(--ak-dark-background);
                }
            }
        `,
    ];

    get classesAndIcon() {
        const chrome = chromeList.find(
            ([level, color]) => this.color === level || this.color === color,
        );

        const [illo, icon] = chrome ? chrome.slice(2) : ["pf-m-grey", "fa-info-circle"];

        return {
            classes: {
                "pf-c-label": true,
                "pf-m-compact": this.compact,
                ...(illo ? { [illo]: true } : {}),
            },
            icon: this.icon ? this.icon : icon,
        };
    }

    render() {
        const { classes, icon } = this.classesAndIcon;

        return html`<span class=${classMap(classes)}>
            <span class="pf-c-label__content">
                <span class="pf-c-label__icon">
                    <i class="fas fa-fw ${icon}" aria-hidden="true"></i>
                </span>
                <slot></slot>
            </span>
        </span>`;
    }
}

export function akLabel(properties: ILabel, content: SlottedTemplateResult = nothing) {
    const message = typeof content === "string" ? html`<span>${content}</span>` : content;
    return html`<ak-label ${spread(properties as Spread)}>${message}</ak-label>`;
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-label": Label;
    }
}
