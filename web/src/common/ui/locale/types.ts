export type LocaleRow = [string, string, string];

export type AkLocale = {
    code: string;
    label: () => string;
    locale: () => Promise<Locale>;
};
