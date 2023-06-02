import { configureLocalization } from "@lit/localize";

import { sourceLocale, targetLocales } from "../../../locale-codes";
import { getBestMatchLocale } from "./helpers";

export const { getLocale, setLocale } = configureLocalization({
    sourceLocale,
    targetLocales,
    loadLocale: async (locale: string) => {
        const localeDef = getBestMatchLocale(locale);
        if (!localeDef) {
            console.warn(`Unrecognized locale: ${localeDef}`);
            return Promise.reject("");
        }
        return localeDef.locale();
    },
});
