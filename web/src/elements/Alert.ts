import { AKElement } from "@goauthentik/elements/Base";
import { type SlottedTemplateResult, type Spread } from "@goauthentik/elements/types";
import { spread } from "@open-wc/lit-helpers";

import { css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export enum Level {
    Warning = "pf-m-warning",
    Info = "pf-m-info",
    Success = "pf-m-success",
    Danger = "pf-m-danger",
}

export const levelNames = ["warning", "info", "success", "danger"];
export type Levels = (typeof levelNames)[number];

export interface IAlert {
    inline?: boolean;
    plain?: boolean;
    icon?: string;
    level?: string;
}

/**
 * @class Alert
 * @element ak-alert
 *
 * Alerts are in-page elements intended to draw the user's attention and alert them to important
 * details. Alerts are used alongside form elements to warn users of potential mistakes they can
 * make, as well as in in-line documentation.
 */
@customElement("ak-alert")
export class Alert extends AKElement implements IAlert {
    /**
     * Whether or not to display the entire component's contents in-line or not.
     *
     * @attr
     */
    @property({ type: Boolean })
    inline = false;

    @property({ type: Boolean })
    plain = false;

    /**
     * Method of determining severity
     *
     * @attr
     */
    @property()
    level: Level | Levels = Level.Warning;

    /**
     * Icon to display
     *
     * @attr
     */
    @property()
    icon = "fa-exclamation-circle";

    static get styles() {
        return [
            PFBase,
            PFAlert,
            css`
                p {
                    margin: 0;
                }
            `,
        ];
    }

    get classmap() {
        const level = levelNames.includes(this.level)
            ? `pf-m-${this.level}`
            : (this.level as string);
        return {
            "pf-c-alert": true,
            "pf-m-inline": this.inline,
            "pf-m-plain": this.plain,
            [level]: true,
        };
    }

    render() {
        return html`<div class="${classMap(this.classmap)}">
            <div class="pf-c-alert__icon">
                <i class="fas ${this.icon}"></i>
            </div>
            <h4 class="pf-c-alert__title"><slot></slot></h4>
        </div>`;
    }
}

export function akAlert(properties: IAlert, content: SlottedTemplateResult = nothing) {
    const message = typeof content === "string" ? html`<span>${content}</span>` : content;
    return html`<ak-alert ${spread(properties as Spread)}>${message}</ak-alert>`;
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-alert": Alert;
    }
}
