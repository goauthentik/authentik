/**
 * @file Implementation code for the Crontab component
 */

import styles from "./Crontab.styles";

import { WithLocale } from "#elements/mixins/locale";
import { type ElementRest } from "#elements/types";

import { spread } from "@open-wc/lit-helpers";
import cronstrue from "cronstrue/i18n";

import { msg } from "@lit/localize";
import { html, LitElement } from "lit";
import { property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

export const localeFallback = "en";

const localeToCronstrue = new Map([
    ["ar", "ar"],
    ["bg-BG", "bg"],
    ["bn-BD", localeFallback],
    ["cs-CZ", "cs"],
    ["de-DE", "de"],
    ["en", "en"],
    ["en-XA", localeFallback],
    ["es-ES", "es"],
    ["fi-FI", "fi"],
    ["fr-FR", "fr"],
    ["it-IT", "it"],
    ["ja-JP", "ja"],
    ["ko-KR", "ko"],
    ["nb-NO", "nb"],
    ["nl-NL", "nl"],
    ["pl-PL", "pl"],
    ["pt-BR", "pt_BR"],
    ["ru-RU", "ru"],
    ["sk-SK", "sk"],
    ["tr-TR", "tr"],
    ["zh-Hans", "zh_CN"],
    ["zh-Hant", "zh_TW"],
]);

/**
 * @element ak-crontab
 * @summary A crontab display
 *
 * @attr {string} cron - The cron string to display as text
 * @attr {boolean} hide-crontab - Set this to show only the explainer text.
 *
 * See the `Crontab.root.css` file in this folder for the CSS Custom Properties that
 * control the appearance of this component.
 */

export class Crontab extends WithLocale(LitElement) {
    static readonly styles = [styles];

    @property({ attribute: "cron" })
    private cronString = "* * * * *";

    @property({ type: Boolean, attribute: "hide-crontab" })
    public hideCrontab = false;

    get label() {
        try {
            return cronstrue.toString(this.cronString, {
                throwExceptionOnParseError: true,
                use24HourTimeFormat: true,
                locale: localeToCronstrue.get(this.activeLanguageTag) ?? "en",
            });
        } catch {
            return msg("Cron string does not parse.", { id: "crontab.parse-failed" });
        }
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
