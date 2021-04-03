import { i18n } from "@lingui/core";
import { en } from "make-plural/plurals";
import { messages as localeEN } from "../locales/en";

i18n.loadLocaleData("en", {
    plurals: en
});
i18n.load("en", localeEN);
i18n.activate("en");
// Uncomment to debug localisation
// import { messages as localeDEBUG } from "../locales/pseudo-LOCALE";
// i18n.load("debug", localeDEBUG);
// i18n.activate("debug");
