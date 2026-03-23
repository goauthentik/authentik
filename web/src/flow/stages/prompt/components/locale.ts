import { TargetLanguageTag } from "#common/ui/locale/definitions";
import {
    formatAutoDetectLocaleDisplayName,
    formatLocaleDisplayNames,
    LocaleDisplay,
} from "#common/ui/locale/format";
import { getBestMatchLocale, getSessionLocale } from "#common/ui/locale/utils";

import { LocaleOptions } from "#elements/locale/utils";
import { LitFC } from "#elements/types";

import { StagePrompt } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { guard } from "lit/directives/guard.js";

// Fixes horizontal rule <hr> warning in select dropdowns.
/* eslint-disable lit/no-invalid-html */

export interface LocalePromptProps {
    activeLanguageTag: TargetLanguageTag;
    prompt: StagePrompt;
    fieldId: string;
    disabled?: boolean;
    debug?: boolean;
}

export const LocalePrompt: LitFC<LocalePromptProps> = ({
    activeLanguageTag,
    prompt,
    disabled,
    debug,
    fieldId,
}) => {
    const sessionLocale = getSessionLocale();

    return guard(
        [activeLanguageTag, prompt.fieldKey, prompt.initialValue, disabled, sessionLocale],
        () => {
            const entries = formatLocaleDisplayNames(activeLanguageTag, {
                debug,
            });

            const languagesByTag = new Map<TargetLanguageTag, LocaleDisplay>(
                entries.map((entry) => [entry[0], entry]),
            );

            const selectedLanguageTag = prompt.initialValue
                ? getBestMatchLocale(prompt.initialValue)
                : null;

            /**
             *  This is a bit subtle.
             *
             * -
             */
            const autoDetectedLocale = formatAutoDetectLocaleDisplayName(
                sessionLocale ? languagesByTag.get(selectedLanguageTag || activeLanguageTag) : null,
            );

            return html`<select
                class="pf-c-form-control ak-m-capitalize"
                id=${fieldId}
                name=${prompt.fieldKey}
                ?disabled=${disabled}
                aria-label=${msg("Select language", {
                    id: "language-selector-label",
                    desc: "Label for the language selection dropdown",
                })}
            >
                <option value="" ?selected=${!selectedLanguageTag}>${autoDetectedLocale}</option>
                <hr />
                ${LocaleOptions({ entries, activeLocaleTag: selectedLanguageTag })}
            </select>`;
        },
    );
};
