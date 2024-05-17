import { AKElement } from "@goauthentik/elements/Base";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import PFLabel from "@patternfly/patternfly/components/Label/label.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export enum PFColor {
    Green = "success",
    Orange = "warning",
    Red = "danger",
    Grey = "info",
}

export const levelNames = ["warning", "info", "success", "danger"];
export type Level = (typeof levelNames)[number];

type Chrome = [Level, PFColor, string, string];
const chromeList: Chrome[] = [
    ["danger", PFColor.Red, "pf-m-red", "fa-times"],
    ["warning", PFColor.Orange, "pf-m-orange", "fa-exclamation-triangle"],
    ["success", PFColor.Green, "pf-m-green", "fa-check"],
    ["info", PFColor.Grey, "pf-m-grey", "fa-info-circle"],
];

export interface ILabel {
    icon?: string;
    compact?: boolean;
    color?: string;
}

/**
 * @class Label
 * @element ak-label
 *
 * Labels are in-page elements for labeling visual elements.
 *
 * @slot - Content of the label
 */
@customElement("ak-label")
export class Label extends AKElement implements ILabel {
    /**
     * The icon to show next to the label
     *
     * @attr
     */
    @property()
    icon?: string;

    /**
     * When true, creates a smaller label with tighter layout
     *
     * @attr
     */
    @property({ type: Boolean })
    compact = false;

    /**
     * Severity level
     *
     * @attr
     */
    @property()
    color: PFColor | Level = PFColor.Grey;

    static get styles(): CSSResult[] {
        return [PFBase, PFLabel];
    }

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

    render(): TemplateResult {
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

declare global {
    interface HTMLElementTagNameMap {
        "ak-label": Label;
    }
}
