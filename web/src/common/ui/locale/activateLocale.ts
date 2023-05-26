import { getLocale, setLocale } from "./configureLocale";
import { getBestMatchLocale, localeFromUrl } from "./helpers";

export function activateLocale(code: string) {
    const urlLocale = localeFromUrl("locale");
    if (urlLocale !== null && urlLocale !== "") {
        code = urlLocale;
    }

    const locale = getBestMatchLocale(code);
    if (!locale) {
        console.warn(`authentik/locale: failed to find locale for code ${code}`);
        return;
    }

    locale.locale().then(() => {
        console.debug(`authentik/locale: Loaded locale '${code}'`);
        if (getLocale() === code) {
            return;
        }
        console.debug(`Setting Locale to ... ${locale.label()} (${locale.code})`);
        setLocale(locale.code);
    });
}

export default activateLocale;
