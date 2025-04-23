import type { LocaleModule } from "@lit/localize";

/**
 * - ISO 639-1 code for the locale.
 * - Pattern to match the user-supplied locale.
 * - Human-readable label for the locale.
 * - Locale loader.
 */
export type LocaleRow = [
    languageCode: string,
    pattern: RegExp,
    formatLabel: () => string,
    fetch: () => Promise<LocaleModule>,
];

export interface AKLocaleDefinition {
    languageCode: string;
    pattern: RegExp;
    formatLabel(): string;
    fetch(): Promise<LocaleModule>;
}
