import { en } from "make-plural/plurals";

import { i18n } from "@lingui/core";

import { messages as localeEN } from "../locales/en";
import { messages as localeDEBUG } from "../locales/pseudo-LOCALE";

i18n.loadLocaleData("en", { plurals: en });
i18n.loadLocaleData("debug", { plurals: en });
i18n.load("en", localeEN);
i18n.load("debug", localeDEBUG);
i18n.activate("en");

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
