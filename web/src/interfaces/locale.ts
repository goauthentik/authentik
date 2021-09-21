import { en } from "make-plural/plurals";

import { i18n } from "@lingui/core";

import { messages as localeEN } from "../locales/en";
import { messages as localeDEBUG } from "../locales/pseudo-LOCALE";

i18n.loadLocaleData("en", { plurals: en });
i18n.loadLocaleData("debug", { plurals: en });
i18n.load("en", localeEN);
i18n.load("debug", localeDEBUG);
i18n.activate("en");

if (window.location.search.includes("debugLocale")) {
    i18n.activate("debug");
}
