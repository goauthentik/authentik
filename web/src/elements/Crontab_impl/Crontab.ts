/**
 * @file Implementation code for the Crontab component
 */

import styles from "./Crontab.styles";
import { decodeCrontab } from "./decodeCrontab";

import { WithLocale } from "#elements/mixins/locale";
import { type ElementRest } from "#elements/types";

import { spread } from "@open-wc/lit-helpers";

import { html, LitElement } from "lit";
import { property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

/**
 * @element ak-crontab
 * @summary A crontab display
 *
 * @attr {string} cron - The cron string to display as text
 * @attr {boolean} hide-crontab - Set this to show only the explainer text.
 *
 * See the `Crontab.root.css` file in this folder for the CSS Custom Properties that control the
 * appearance of this component.
 */

export class Crontab extends WithLocale(LitElement) {
    static readonly styles = [styles];

    @property({ attribute: "cron" })
    public cronString = "* * * * *";

    @property({ type: Boolean, attribute: "hide-crontab" })
    public hideCrontab = false;

    get label() {
        return decodeCrontab(this.cronString, this.activeLanguageTag);
    }

    render() {
        return html`<div part="crontab">
            ${
                this.hideCrontab
                    ? html`<div part="natural">${this.label}</div>`
                    : html`<code part="cronstring">${this.cronString}</code>
                          <div part="natural">${this.label}</div>`
            }
        </div>`;
    }
}

export type CrontabProps = ElementRest & {
    cron?: string;
    hideCrontab?: boolean;
};

/**
 * @returns {TemplateResult} A Lit template result containing the configured ak-crontab element
 * @summary Helper function to create a Crontab component programmatically
 *
 * @see {@link Crontab} - The underlying web component
 */
export function akCrontab(options: CrontabProps = {}) {
    const { cron, hideCrontab, ...rest } = options;

    return html`
        <ak-crontab
            ${spread(rest)}
            ?hide-crontab=${hideCrontab}
            cron=${ifDefined(cron)}
        ></ak-crontab>
    `;
}
