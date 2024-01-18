import type { LocaleModule } from "@lit/localize";

export type LocaleRow = [string, RegExp, () => string, () => Promise<LocaleModule>];

export type AkLocale = {
    code: string;
    match: RegExp;
    label: () => string;
    locale: () => Promise<LocaleModule>;
};
