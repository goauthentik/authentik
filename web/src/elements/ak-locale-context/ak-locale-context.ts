import { AKElement } from "@goauthentik/elements/Base";

import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { WithBrandConfig } from "../Interface/brandProvider";
import { initializeLocalization } from "./configureLocale.js";
import type { GetLocale, SetLocale } from "./configureLocale.js";
import { EVENT_LOCALE_CHANGE, EVENT_LOCALE_REQUEST, LocaleContextEventDetail } from "./events.js";
import { DEFAULT_LOCALE, autoDetectLanguage, findLocaleDefinition } from "./helpers.js";

/**
 * A component to manage your locale settings.
 *
 * @remarks
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
    protected static singleton: LocaleContext | null = null;

    /**
     * The text representation of the current locale
     * @attribute
     */
    @property({ attribute: true, type: String })
    public locale = DEFAULT_LOCALE;

    /**
     * The URL parameter to look for (if any)
     * @attribute
     */
    @property({ attribute: true, type: String })
    public param = "locale";

    protected readonly getLocale: GetLocale;
    protected readonly setLocale: SetLocale;

    constructor(code = DEFAULT_LOCALE) {
        super();

        if (LocaleContext.singleton) {
            throw new Error(`Developer error: Must have only one locale context per session`);
        }

        LocaleContext.singleton = this;

        const [getLocale, setLocale] = initializeLocalization();

        this.getLocale = getLocale;
        this.setLocale = setLocale;

        this.setLocale(code).then(this.#notifyApplication);
    }

    connectedCallback() {
        this.#updateLocale();

        window.addEventListener(EVENT_LOCALE_REQUEST, this.#localeUpdateListener as EventListener);
    }

    disconnectedCallback() {
        LocaleContext.singleton = null;

        window.removeEventListener(
            EVENT_LOCALE_REQUEST,
            this.#localeUpdateListener as EventListener,
        );
        super.disconnectedCallback();
    }

    #localeUpdateListener = (ev: CustomEvent<LocaleContextEventDetail>) => {
        console.debug("authentik/locale: Locale update request received.");
        this.#updateLocale(ev.detail.locale);
    };

    #updateLocale(requestedLanguageCode?: string) {
        const localeRequest = autoDetectLanguage(requestedLanguageCode, this.brand?.defaultLocale);

        const locale = findLocaleDefinition(localeRequest);

        if (!locale) {
            console.warn(`authentik/locale: failed to find locale for code ${localeRequest}`);
            return;
        }

        return locale.fetch().then(() => {
            console.debug(
                `authentik/locale: Setting Locale to ${locale.formatLabel()} (${locale.languageCode})`,
            );

            this.setLocale(locale.languageCode).then(this.#notifyApplication);
        });
    }

    #notifyFrameID = -1;

    #notifyApplication = () => {
        cancelAnimationFrame(this.#notifyFrameID);

        requestAnimationFrame(() => {
            // You will almost never have cause to catch this event.
            // Lit's own `@localized()` decorator works just fine for almost every use case.
            this.dispatchEvent(
                new CustomEvent(EVENT_LOCALE_CHANGE, {
                    bubbles: true,
                    composed: true,
                }),
            );
        });
    };

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
