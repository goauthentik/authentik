import type { TargetLanguageTag } from "#common/ui/locale/definitions";

import cronstrue from "cronstrue/i18n";

import { msg } from "@lit/localize";

const localeFallback = "en";

const localeToCronstrue: Record<TargetLanguageTag, string> = {
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
        if (!isValidDjangoCron(value)) throw new Error("Not a server-accepted crontab");

        return cronstrue.toString(value, {
            throwExceptionOnParseError: true,
            use24HourTimeFormat: true,
            locale: localeToCronstrue[language] ?? localeFallback,
        });
    } catch {
        return msg("Cron string does not parse.", { id: "crontab.parse-failed" });
    }
}
