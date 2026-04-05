import { PseudoLanguageTag, TargetLanguageTag } from "#common/ui/locale/definitions";
import { formatRelativeLocaleDisplayName, LocaleDisplay } from "#common/ui/locale/format";

import type { LitFC, SlottedTemplateResult } from "#elements/types";

import { html } from "lit";
import { repeat } from "lit/directives/repeat.js";

export interface LocaleOptionsProps {
    entries: Iterable<LocaleDisplay>;
    activeLocaleTag: TargetLanguageTag | null;
}

/**
 * Render locale display name options for a select element.
 */
export const LocaleOptions: LitFC<LocaleOptionsProps> = ({ entries, activeLocaleTag }) => {
    return repeat(
        entries,
        ([languageTag]) => languageTag,
        ([languageTag, localizedDisplayName, relativeDisplayName]) => {
            const pseudo = languageTag === PseudoLanguageTag;

            const localizedMessage = formatRelativeLocaleDisplayName(
                languageTag,
                localizedDisplayName,
                relativeDisplayName,
            );

            return html`${pseudo ? html`<hr />` : null}
                <option value=${languageTag} ?selected=${languageTag === activeLocaleTag}>
                    ${localizedMessage}
                </option>`;
        },
    ) as SlottedTemplateResult;
};
