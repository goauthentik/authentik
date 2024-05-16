import { AKElement } from "@goauthentik/elements/Base";

import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export interface IAlert {
    inline?: boolean;
    warning?: boolean;
    info?: boolean;
    success?: boolean;
    danger?: boolean;
}

export enum Level {
    Warning = "pf-m-warning",
    Info = "pf-m-info",
    Success = "pf-m-success",
    Danger = "pf-m-danger",
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

    /**
     * Fallback method of determining severity
     *
     * @attr
     */
    @property()
    level: Level = Level.Warning;

    /**
     * Highest severity level.
     *
     * @attr
     */
    @property({ type: Boolean })
    danger = false;

    /**
     * Next severity level.
     *
     * @attr
     */
    @property({ type: Boolean })
    warning = false;

    /**
     * Next severity level. The default severity level.
     *
     * @attr
     */
    @property({ type: Boolean })
    success = false;

    /**
     * Lowest severity level.
     *
     * @attr
     */
    @property({ type: Boolean })
    info = false;

    static get styles() {
        return [PFBase, PFAlert];
    }

    get classmap() {
        const leveltags = ["danger", "warning", "success", "info"].filter(
            // @ts-ignore
            (level) => this[level] && this[level] === true,
        );

        if (leveltags.length > 1) {
            console.warn("ak-alert has multiple levels defined");
        }
        const level = leveltags.length > 0 ? `pf-m-${leveltags[0]}` : this.level;

        return {
            "pf-c-alert": true,
            "pf-m-inline": this.inline,
            [level]: true,
        };
    }

    render() {
        return html`<div class="${classMap(this.classmap)}">
            <div class="pf-c-alert__icon">
                <i class="fas fa-exclamation-circle"></i>
            </div>
            <h4 class="pf-c-alert__title">
                <slot></slot>
            </h4>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-alert": Alert;
    }
}
