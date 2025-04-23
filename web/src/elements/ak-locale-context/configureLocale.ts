import { configureLocalization } from "@lit/localize";

import { sourceLocale, targetLocales } from "../../locale-codes.js";
import { findLocaleDefinition } from "./helpers.js";

export type ConfigureLocalizationResult = ReturnType<typeof configureLocalization>;

export type GetLocale = ConfigureLocalizationResult["getLocale"];
export type SetLocale = ConfigureLocalizationResult["setLocale"];

export type LocaleState = [GetLocale, SetLocale];

let cachedLocaleState: LocaleState | undefined = undefined;

/**
 * This is where the lit-localization module is initialized with our loader,
 * which associates our collection of locales with its getter and setter functions.
 *
 * @returns A tuple of getter and setter functions.
 * @internal
 */
export function initializeLocalization(): LocaleState {
    if (cachedLocaleState) return cachedLocaleState;

    const { getLocale, setLocale } = configureLocalization({
        sourceLocale,
        targetLocales,
        loadLocale: (languageCode) => {
            const localeDef = findLocaleDefinition(languageCode);

            if (!localeDef) {
                throw new Error(`Unrecognized locale: ${localeDef}`);
            }

            return localeDef.fetch();
        },
    });

    cachedLocaleState = [getLocale, setLocale];

    return cachedLocaleState;
}

export default initializeLocalization;
