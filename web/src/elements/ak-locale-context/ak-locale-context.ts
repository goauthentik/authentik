import { EVENT_LOCALE_CHANGE, EVENT_LOCALE_REQUEST } from "@goauthentik/common/constants.js";
import { AKElement } from "@goauthentik/elements/Base";
import { customEvent } from "@goauthentik/elements/utils/customEvents";

import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { WithBrandConfig } from "../Interface/brandProvider";
import { initializeLocalization } from "./configureLocale";
import type { LocaleGetter, LocaleSetter } from "./configureLocale";
import { DEFAULT_LOCALE, autoDetectLanguage, getBestMatchLocale } from "./helpers";

/**
 * A component to manage your locale settings.
 *
 * ## Details
 *
 * This component exists to take a locale setting from several different places, find the
 * appropriate locale file in our catalog of locales, and set the lit-localization context
 * appropriately. If that works, it sends off an event saying so.
 *
 * @element ak-locale-context
 * @slot - The content which consumes this context
 * @fires ak-locale-change - When a valid locale has been swapped in
 */
@customElement("ak-locale-context")
export class LocaleContext extends WithBrandConfig(AKElement) {
    /// @attribute The text representation of the current locale */
    @property({ attribute: true, type: String })
    locale = DEFAULT_LOCALE;

    /// @attribute The URL parameter to look for (if any)
    @property({ attribute: true, type: String })
    param = "locale";

    getLocale: LocaleGetter;

    setLocale: LocaleSetter;

    constructor(code = DEFAULT_LOCALE) {
        super();
        this.notifyApplication = this.notifyApplication.bind(this);
        this.updateLocaleHandler = this.updateLocaleHandler.bind(this);
        try {
            const [getLocale, setLocale] = initializeLocalization();
            this.getLocale = getLocale;
            this.setLocale = setLocale;
            this.setLocale(code).then(() => {
                window.setTimeout(this.notifyApplication, 0);
            });
        } catch (e) {
            throw new Error(`Developer error: Must have only one locale context per session: ${e}`);
        }
    }

    connectedCallback() {
        super.connectedCallback();
        this.updateLocale();
        window.addEventListener(EVENT_LOCALE_REQUEST, this.updateLocaleHandler as EventListener);
    }

    disconnectedCallback() {
        window.removeEventListener(EVENT_LOCALE_REQUEST, this.updateLocaleHandler as EventListener);
        super.disconnectedCallback();
    }

    updateLocaleHandler(ev: CustomEvent<{ locale: string }>) {
        console.debug("authentik/locale: Locale update request received.");
        this.updateLocale(ev.detail.locale);
    }

    updateLocale(requestedLocale: string | undefined = undefined) {
        const localeRequest = autoDetectLanguage(requestedLocale, this.brand?.defaultLocale);
        const locale = getBestMatchLocale(localeRequest);
        if (!locale) {
            console.warn(`authentik/locale: failed to find locale for code ${localeRequest}`);
            return;
        }
        locale.locale().then(() => {
            console.debug(`authentik/locale: Setting Locale to ${locale.label()} (${locale.code})`);
            this.setLocale(locale.code).then(() => {
                window.setTimeout(this.notifyApplication, 0);
            });
        });
    }

    notifyApplication() {
        // You will almost never have cause to catch this event. Lit's own `@localized()` decorator
        // works just fine for almost every use case.
        this.dispatchEvent(customEvent(EVENT_LOCALE_CHANGE));
    }

    render() {
        return html`<slot></slot>`;
    }
}

export default LocaleContext;

declare global {
    interface HTMLElementTagNameMap {
        "ak-locale-context": LocaleContext;
    }
}
