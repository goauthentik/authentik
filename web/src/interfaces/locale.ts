import { en, es, fr, pl, tr, zh } from "make-plural/plurals";

import { Messages, i18n } from "@lingui/core";
import { detect, fromNavigator, fromStorage, fromUrl } from "@lingui/detect-locale";
import { t } from "@lingui/macro";

import { messages as localeEN } from "../locales/en";
import { messages as localeES } from "../locales/es";
import { messages as localeFR_FR } from "../locales/fr_FR";
import { messages as localePL } from "../locales/pl";
import { messages as localeDEBUG } from "../locales/pseudo-LOCALE";
import { messages as localeTR } from "../locales/tr";
import { messages as localeZH_Hans } from "../locales/zh-Hans";
import { messages as localeZH_Hant } from "../locales/zh-Hant";
import { messages as localeZH_TW } from "../locales/zh_TW";

export const LOCALES: {
    code: string;
    label: string;
    // eslint-disable-next-line @typescript-eslint/ban-types
    plurals: Function;
    locale: Messages;
}[] = [
    {
        code: "en",
        plurals: en,
        label: t`English`,
        locale: localeEN,
    },
    {
        code: "debug",
        plurals: en,
        label: t`Debug`,
        locale: localeDEBUG,
    },
    {
        code: "fr",
        plurals: fr,
        label: t`French`,
        locale: localeFR_FR,
    },
    {
        code: "tr",
        plurals: tr,
        label: t`Turkish`,
        locale: localeTR,
    },
    {
        code: "es",
        plurals: es,
        label: t`Spanish`,
        locale: localeES,
    },
    {
        code: "pl",
        plurals: pl,
        label: t`Polish`,
        locale: localePL,
    },
    {
        code: "zh_TW",
        plurals: zh,
        label: t`Taiwanese Mandarin`,
        locale: localeZH_TW,
    },
    {
        code: "zh-Hans",
        plurals: zh,
        label: t`Chinese (simplified)`,
        locale: localeZH_Hans,
    },
    {
        code: "zh-Hant",
        plurals: zh,
        label: t`Chinese (traditional)`,
        locale: localeZH_Hant,
    },
];

LOCALES.forEach((locale) => {
    i18n.loadLocaleData(locale.code, { plurals: locale.plurals });
    i18n.load(locale.code, locale.locale);
});

const DEFAULT_FALLBACK = () => "en";

export function autoDetectLanguage() {
    let detected =
        detect(fromUrl("lang"), fromStorage("lang"), fromNavigator(), DEFAULT_FALLBACK) ||
        DEFAULT_FALLBACK();
    // For now we only care about the first locale part
    if (detected.includes("_")) {
        detected = detected.split("_")[0];
    }
    if (detected in i18n._messages) {
        console.debug(`authentik/locale: Activating detected locale '${detected}'`);
        i18n.activate(detected);
    } else {
        console.debug(`authentik/locale: No locale for '${detected}', falling back to en`);
        i18n.activate(DEFAULT_FALLBACK());
    }
}
autoDetectLanguage();
