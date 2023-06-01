import type { LocaleModule } from "@lit/localize";

export type LocaleRow = [string, () => string, () => Promise<LocaleModule>];

export type AkLocale = {
    code: string;
    label: () => string;
    locale: () => Promise<LocaleModule>;
};
