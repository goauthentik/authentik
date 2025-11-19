import type { LocaleModule } from "@lit/localize";

export type LocaleRow = [
    code: string,
    pattern: RegExp,
    label: () => string,
    loader: () => Promise<LocaleModule>,
];

export type AkLocale = {
    code: string;
    match: RegExp;
    label: () => string;
    locale: () => Promise<LocaleModule>;
};
