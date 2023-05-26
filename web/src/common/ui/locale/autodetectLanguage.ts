import { globalAK } from "@goauthentik/common/global";

import { activateLocale } from "./activateLocale";
import { setLocale } from "./configureLocale";
import { DEFAULT_FALLBACK } from "./definitions";
import { findSupportedLocale, localeFromUrl } from "./helpers";

export function autoDetectLanguage(defaultLanguage: string) {
    // Always load en locale at the start so we have something and don't error
    setLocale("en");

    // Get all locales we can, in order
    // - Global authentik settings (contains user settings)
    // - URL parameter
    // - Navigator
    // - Fallback (en)

    const localeCandidates = [
        globalAK()?.locale,
        localeFromUrl("locale"),
        window.navigator.language,
        DEFAULT_FALLBACK,
    ].filter((v) => v && v !== "");

    const firstSupportedLocale = findSupportedLocale(localeCandidates);

    if (!firstSupportedLocale) {
        console.debug(`authentik/locale: No locale for '${locales}', falling back to en`);
        activateLocale(defaultLanguage);
        return;
    }

    activateLocale(firstSupportedLocale.code);
}

export default autoDetectLanguage;
