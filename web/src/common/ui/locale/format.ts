import { allLocales } from "../../../locale-codes.js";

import { LanguageTag, TargetLanguageTag } from "#common/ui/locale/definitions";
import { isCJKLanguageTag, isHanLanguageTag } from "#common/ui/locale/utils";

import { msg, str } from "@lit/localize";
import { html } from "lit";
import { repeat } from "lit/directives/repeat.js";

export function createLocale(
    locale?: Intl.Locale | Intl.UnicodeBCP47LocaleIdentifier,
    options?: Intl.LocaleOptions,
): Intl.Locale {
    if (!locale) {
        return new Intl.Locale(LanguageTag.Source);
    }

    return typeof locale === "string" ? new Intl.Locale(locale, options) : locale;
}

export function formatDisplayName(
    localeID: Intl.Locale | Intl.UnicodeBCP47LocaleIdentifier,
    fallback?: string,
    languageNames?: Intl.DisplayNames,
): string {
    localeID = typeof localeID === "string" ? localeID : localeID.baseName;
    fallback ??= localeID;

    languageNames ??= new Intl.DisplayNames([localeID], {
        type: "language",
    });

    try {
        return languageNames.of(localeID) || fallback;
    } catch (_error) {
        return fallback;
    }
}

/**
 * Given a localized display name, normalize it for comparison or sorting,
 * removing diacritics and other marks.
 */
export function normalizeDisplayName(displayName: string): string {
    return displayName
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase();
}

/**
 * A triple representing a locale and its corresponding display names.
 */
export type LocaleDisplay = [
    locale: Intl.UnicodeBCP47LocaleIdentifier,
    localizedDisplayName: string,
    relativeDisplayName: string,
];

export function createIntlCollator(
    activeLocale: Intl.UnicodeBCP47LocaleIdentifier,
    options: Intl.CollatorOptions,
) {
    return ([aLocale, aName]: LocaleDisplay, [bLocale, bName]: LocaleDisplay) => {
        // The current locale always goes first.

        if (activeLocale === aLocale) {
            return -1;
        }

        if (activeLocale === bLocale) {
            return 1;
        }

        // Pseudo locale goes last....

        if (LanguageTag.Pseudo === aLocale) {
            return 1;
        }

        if (LanguageTag.Pseudo === bLocale) {
            return -1;
        }

        if (isCJKLanguageTag(aLocale) && !isCJKLanguageTag(bLocale)) {
            return 1;
        }

        if (!isCJKLanguageTag(aLocale) && isCJKLanguageTag(bLocale)) {
            return -1;
        }

        // Finally, sort by localized name.

        return aName.localeCompare(bName, activeLocale, options);
    };
}

export interface FormatLocaleOptionsInit {
    activeLocale?: Intl.UnicodeBCP47LocaleIdentifier | Intl.Locale;
    languageNames?: Intl.DisplayNames;
    collatorOptions?: Intl.CollatorOptions;
    debug?: boolean;
}

/**
 * Format the locale options for use in a user-facing element.
 *
 * @returns An array of locale options sorted by their labels.
 */
export function formatLocaleDisplayNames(
    activeLanguageTag: Intl.UnicodeBCP47LocaleIdentifier | Intl.Locale,
    { collatorOptions = {}, languageNames, debug }: FormatLocaleOptionsInit = {},
): LocaleDisplay[] {
    const activeLocale = createLocale(activeLanguageTag);

    languageNames ??= new Intl.DisplayNames(activeLocale, {
        type: "language",
    });

    const localeIDs = new Set<Intl.UnicodeBCP47LocaleIdentifier>();

    const displayNames = new Map<Intl.UnicodeBCP47LocaleIdentifier, string>([
        [
            LanguageTag.Source,
            formatDisplayName(LanguageTag.Source, msg("English", { id: "en" }), languageNames),
        ],
        [
            LanguageTag.HanSimplified,
            formatDisplayName(
                LanguageTag.HanSimplified,
                msg("Chinese (Simplified)", { id: "zh-Hans" }),
                languageNames,
            ),
        ],
        [
            LanguageTag.HanTraditional,
            formatDisplayName(
                LanguageTag.HanTraditional,
                msg("Chinese (Traditional)", { id: "zh-Hant" }),
                languageNames,
            ),
        ],
        [
            LanguageTag.Japanese,
            formatDisplayName(
                new Intl.Locale(LanguageTag.Japanese).minimize(),
                msg("Japanese", { id: "ja-JP" }),
                languageNames,
            ),
        ],

        [
            LanguageTag.Korean,
            formatDisplayName(
                new Intl.Locale(LanguageTag.Korean).minimize(),
                msg("Korean", { id: "ko-KR" }),
                languageNames,
            ),
        ],
    ]);

    const tags = new Set(allLocales);
    const localeCache = new Map<Intl.UnicodeBCP47LocaleIdentifier, Intl.Locale>();

    for (const tag of tags) {
        if (displayNames.has(tag) || tag === LanguageTag.Pseudo) {
            continue;
        }

        let locale = localeCache.get(tag);

        if (!locale) {
            locale = new Intl.Locale(tag);
            localeCache.set(tag, locale);
        }

        let localeID: string;

        // Prefer a less specific locale ID if we haven't already used it.
        if (!localeIDs.has(locale.language)) {
            localeID = locale.language;
        } else {
            localeID = locale.baseName;
        }

        localeIDs.add(localeID);

        displayNames.set(tag, formatDisplayName(localeID, locale.language, languageNames));
    }

    if (debug) {
        displayNames.set(
            LanguageTag.Pseudo,
            formatDisplayName(
                LanguageTag.Pseudo,
                // Fallback provided if the browser doesn't support this locale.
                msg("English (Pseudo-Accents)", { id: "en-XA" }),
                languageNames,
            ),
        );
    }

    const entries = Array.from(displayNames)
        .map(([languageTag, localizedDisplayName]): LocaleDisplay => {
            const relativeLanguageNames = new Intl.DisplayNames(languageTag, {
                type: "language",
            });

            const locale = localeCache.get(languageTag) || new Intl.Locale(languageTag);
            const localeID = isHanLanguageTag(languageTag) ? locale.baseName : locale.language;

            const relativeDisplayName = formatDisplayName(
                localeID,
                localizedDisplayName,
                relativeLanguageNames,
            );

            return [languageTag, localizedDisplayName, relativeDisplayName];
        })

        .sort(createIntlCollator(activeLocale.baseName, collatorOptions));

    return entries;
}

export function renderLocaleDisplayNames(
    entries: LocaleDisplay[],
    activeLocaleTag: TargetLanguageTag | null,
) {
    return repeat(
        entries,
        ([languageTag]) => languageTag,
        ([languageTag, localizedDisplayName, relativeDisplayName]) => {
            const pseudo = languageTag === LanguageTag.Pseudo;

            const same =
                relativeDisplayName &&
                normalizeDisplayName(relativeDisplayName) ===
                    normalizeDisplayName(localizedDisplayName);

            let localizedMessage = localizedDisplayName;

            if (!same && !pseudo) {
                localizedMessage = msg(str`${relativeDisplayName} (${localizedDisplayName})`, {
                    id: "locale-option-localized-label",
                    desc: "Locale option label showing the localized language name along with the native language name in parentheses. The first placeholder is the localized language name, the second is the relative language name.",
                });
            }

            return html`${pseudo ? html`<hr />` : null}
                <option value=${languageTag} ?selected=${languageTag === activeLocaleTag}>
                    ${localizedMessage}
                </option>`;
        },
    );
}
