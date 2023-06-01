import { globalAK } from "@goauthentik/common/global";

import { activateLocale } from "./activateLocale";
import { setLocale } from "./configureLocale";
import { DEFAULT_FALLBACK } from "./definitions";
import { findSupportedLocale, localeFromUrl } from "./helpers";

const isLocaleCandidate = (v: unknown): v is string => typeof v === "string" && v !== "";

export function autoDetectLanguage(defaultLanguage = "en") {
    // Always load en locale at the start so we have something and don't error
    setLocale(defaultLanguage);

    // Get all locales we can, in order
    // - Global authentik settings (contains user settings)
    // - URL parameter
    // - Navigator
    // - Fallback (en)

    const localeCandidates: string[] = [
        globalAK()?.locale,
        localeFromUrl("locale"),
        window.navigator.language,
        DEFAULT_FALLBACK,
    ].filter(isLocaleCandidate);

    const firstSupportedLocale = findSupportedLocale(localeCandidates);

    if (!firstSupportedLocale) {
        console.debug(`authentik/locale: No locale for '${localeCandidates}', falling back to en`);
        activateLocale(defaultLanguage);
        return;
    }

    activateLocale(firstSupportedLocale.code);
}

export default autoDetectLanguage;
