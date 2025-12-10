import { sourceLocale, targetLocales } from "../../locale-codes.js";

import { LocaleLabelRecord, LocaleLoaderRecord, TargetLocale } from "#common/ui/locale/definitions";
import { autoDetectLanguage } from "#common/ui/locale/utils";

import { kAKLocale, LocaleContext, LocaleMixin } from "#elements/mixins/locale";
import type { ReactiveElementHost } from "#elements/types";

import { ContextProvider } from "@lit/context";
import { configureLocalization, LOCALE_STATUS_EVENT, LocaleStatusEventDetail } from "@lit/localize";
import type { ReactiveController } from "lit";

/**
 * A controller that provides the application configuration to the element.
 */
export class LocaleContextController implements ReactiveController {
    protected static DocumentObserverInit: MutationObserverInit = {
        attributes: true,
        attributeFilter: ["lang"],
        attributeOldValue: true,
    };

    #log = console.debug.bind(console, `authentik/controller/locale`);

    /**
     * Attempts to apply the given locale code.
     * @param nextLocale A user or agent preferred locale code.
     */
    #applyLocale(nextLocale: TargetLocale) {
        const currentLocale = this.#context.value.getLocale();
        const label = LocaleLabelRecord[nextLocale]();

        if (currentLocale === nextLocale) {
            this.#log("Skipping locale update, already set to:", label);
            return;
        }

        this.#context.value.setLocale(nextLocale);
        this.#host.locale = nextLocale;

        this.#log("Applied locale:", label);
    }

    // #region Attribute Observation

    /**
     * Synchronizes changes to the document's `lang` attribute to the locale context.
     *
     * @remarks
     * While we don't expect the document's `lang` attribute to change outside of
     * this controller, we observe it to respect a possible external change,
     * such as from the user agent's language settings, or a browser extension which
     * modifies the attribute.
     */
    #attributeListener = (mutations: MutationRecord[]) => {
        for (const mutation of mutations) {
            if (mutation.type !== "attributes" || mutation.attributeName !== "lang") {
                continue;
            }

            const attribute = {
                previous: mutation.oldValue,
                current: document.documentElement.lang,
            };

            this.#log("Detected document `lang` attribute change", attribute);

            if (attribute.previous === attribute.current) {
                this.#log("Skipping locale update, `lang` unchanged", attribute);
                continue;
            }

            const nextLocale = autoDetectLanguage(attribute.current);

            this.#applyLocale(nextLocale);

            return;
        }
    };

    #documentObserver = new MutationObserver(this.#attributeListener);

    #connectDocumentObserver() {
        this.#documentObserver.observe(
            document.documentElement,
            LocaleContextController.DocumentObserverInit,
        );
    }

    #disconnectDocumentObserver() {
        this.#documentObserver.disconnect();
    }

    //#endregion

    //#region Lifecycle

    /**
     * Loads the locale module for the given locale code.
     *
     * @param _locale The locale code to load.
     *
     * @remarks
     * This is used by `@lit/localize` to dynamically load locale modules,
     * as well synchronizing the document's `lang` attribute.
     */
    #loadLocale = (_locale: string) => {
        // TypeScript cannot infer the type here, but Lit Localize will only call this
        // function with one of the `targetLocales`.
        const locale = _locale as TargetLocale;
        const label = LocaleLabelRecord[locale]();

        this.#log(`Loading "${label}" module...`);

        const loader = LocaleLoaderRecord[locale];

        return loader();
    };

    #host: ReactiveElementHost<LocaleMixin>;
    #context: ContextProvider<LocaleContext>;

    /**
     * @param host The host element.
     * @param localeHint The initial locale code to set.
     */
    constructor(host: ReactiveElementHost<LocaleMixin>, localeHint?: string) {
        this.#host = host;

        const contextValue = configureLocalization({
            sourceLocale,
            targetLocales,
            loadLocale: this.#loadLocale,
        });

        this.#context = new ContextProvider(this.#host, {
            context: LocaleContext,
            initialValue: contextValue,
        });

        this.#host[kAKLocale] = contextValue;

        const nextLocale = autoDetectLanguage(localeHint);

        if (nextLocale !== sourceLocale) {
            this.#applyLocale(nextLocale);
        }
    }

    #localeStatusListener = (event: CustomEvent<LocaleStatusEventDetail>) => {
        if (event.detail.status === "error") {
            this.#log("Error loading locale:", event.detail);
            return;
        }

        if (event.detail.status === "loading") {
            return;
        }

        const { readyLocale } = event.detail;
        this.#log(`Updating \`lang\` attribute to: \`${readyLocale}\``);

        // Prevent observation while we update the `lang` attribute...
        this.#disconnectDocumentObserver();

        document.documentElement.lang = readyLocale;

        this.#connectDocumentObserver();
    };

    public hostConnected() {
        window.addEventListener(LOCALE_STATUS_EVENT, this.#localeStatusListener);
    }

    public hostDisconnected() {
        this.#documentObserver.disconnect();
        window.removeEventListener(LOCALE_STATUS_EVENT, this.#localeStatusListener);
    }

    //#endregion
}
