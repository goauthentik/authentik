import type { TargetLanguageTag } from "#common/ui/locale/definitions";

import type * as CronstrueLocales from "cronstrue/dist/i18n/allLocales";
import cronstrue from "cronstrue/i18n";

import { msg } from "@lit/localize";

const localeFallback = "en";

export type CronstrueLocale = keyof typeof CronstrueLocales;

// Cronstrue has its own internationalization library, and its own set of tokens for identifying
// locales. This maps our i18n tokens to those of Cronstrue. It is *exhaustive*; if we add a new
// language to authentik but don't record its equivalent here (even if it is the fallback), this
// will fail to type-check.
//
const localeToCronstrue: Record<TargetLanguageTag, CronstrueLocale> = {
    "ar": "ar",
    "bg-BG": "bg",
    "bn-BD": localeFallback,
    "cs-CZ": "cs",
    "da-DK": "da",
    "de-DE": "de",
    "en": "en",
    "en-XA": localeFallback,
    "es-ES": "es",
    "fi-FI": "fi",
    "fr-FR": "fr",
    "it-IT": "it",
    "ja-JP": "ja",
    "ko-KR": "ko",
    "lv-LV": localeFallback,
    "nb-NO": "nb",
    "nl-NL": "nl",
    "pl-PL": "pl",
    "pt-BR": "pt_BR",
    "ru-RU": "ru",
    "sk-SK": "sk",
    "tr-TR": "tr",
    "zh-Hans": "zh_CN",
    "zh-Hant": "zh_TW",
};

const numericToken = /^(\*|\d+)$/;
const namedToken = /^(\*|\d+|[A-Za-z]{3})$/;

export function isValidDjangoCron(value: string): boolean {
    const fields = value.trim().split(/\s+/);

    if (fields.length !== 5) {
        return false;
    }

    return fields.every((field, index) => {
        const token = index < 3 ? numericToken : namedToken;

        return field.split(/[,/-]/).every((part) => token.test(part));
    });
}

export function decodeCrontab(value: string, language: TargetLanguageTag): string {
    try {
        if (!isValidDjangoCron(value)) {
            throw new TypeError(`Not a server-accepted crontab: ${value}`);
        }

        return cronstrue.toString(value, {
            throwExceptionOnParseError: true,
            use24HourTimeFormat: true,
            locale: localeToCronstrue[language] ?? localeFallback,
        });
    } catch {
        return msg("Cron string does not parse.", { id: "crontab.parse-failed" });
    }
}
