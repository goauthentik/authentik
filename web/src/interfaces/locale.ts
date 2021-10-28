import { en, fr } from "make-plural/plurals";

import { i18n } from "@lingui/core";
import { detect, fromNavigator, fromStorage, fromUrl } from "@lingui/detect-locale";

import { messages as localeEN } from "../locales/en";
import { messages as localeFR_FR } from "../locales/fr_FR";
import { messages as localeDEBUG } from "../locales/pseudo-LOCALE";

i18n.loadLocaleData("en", { plurals: en });
i18n.loadLocaleData("debug", { plurals: en });
i18n.loadLocaleData("fr_FR", { plurals: fr });
i18n.load("en", localeEN);
i18n.load("fr_FR", localeFR_FR);
i18n.load("debug", localeDEBUG);

const DEFAULT_FALLBACK = () => "en";

const detected =
    detect(fromUrl("lang"), fromStorage("lang"), fromNavigator(), DEFAULT_FALLBACK) ||
    DEFAULT_FALLBACK();
if (detected in i18n._messages) {
    console.debug(`authentik/locale: Activating detected locale '${detected}'`);
    i18n.activate(detected);
} else {
    console.debug(`authentik/locale: No locale for '${detected}', falling back to en`);
    i18n.activate(DEFAULT_FALLBACK());
}
