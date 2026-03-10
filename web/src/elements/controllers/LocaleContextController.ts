import { SourceLanguageTag } from "#common/ui/locale/definitions";
import { formatDisplayName } from "#common/ui/locale/format";
import { LocaleLoader, LocaleLoaderInit } from "#common/ui/locale/loaders";
import { autoDetectLanguage } from "#common/ui/locale/utils";

import { kAKLocale, LocaleContext, LocaleContextValue, LocaleMixin } from "#elements/mixins/locale";
import type { ReactiveElementHost } from "#elements/types";

import { ConsoleLogger } from "#logger/browser";

import { ContextProvider } from "@lit/context";
import { configureLocalization, LOCALE_STATUS_EVENT, LocaleStatusEventDetail } from "@lit/localize";
import type { ReactiveController } from "lit";

const logger = ConsoleLogger.prefix("controller/locale");

/**
 * A controller that provides the application configuration to the element.
 */
export class LocaleContextController implements ReactiveController {
    /**
     * A shared locale context value.
     */
    static #localizationContext: LocaleContextValue;

    protected static DocumentObserverInit: MutationObserverInit = {
        attributes: true,
        attributeFilter: ["lang"],
        attributeOldValue: true,
    };

    public readonly sourceLocale: string;

    public get activeLanguageTag(): Intl.UnicodeBCP47LocaleIdentifier {
        return LocaleContextController.#localizationContext!.getLocale() as Intl.UnicodeBCP47LocaleIdentifier;
    }

    public set activeLanguageTag(value: Intl.UnicodeBCP47LocaleIdentifier) {
        LocaleContextController.#localizationContext!.setLocale(value);
    }

    /**
     * Attempts to apply the given locale code.
     * @param nextLocale A user or agent preferred locale code.
     */
    #applyLocale(nextLocale: Intl.UnicodeBCP47LocaleIdentifier) {
        const { activeLanguageTag } = this;

        const languageNames = new Intl.DisplayNames([nextLocale, this.sourceLocale], {
            type: "language",
        });

        const displayName = formatDisplayName(nextLocale, nextLocale, languageNames);

        if (activeLanguageTag === nextLocale) {
            logger.debug("Skipping locale update, already set to:", displayName);
            return;
        }

        this.#context.value.setLocale(nextLocale);
        this.#host.activeLanguageTag = nextLocale;

        logger.info("Applied locale:", displayName);
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

            logger.debug("Detected document `lang` attribute change", attribute);

            if (attribute.previous === attribute.current) {
                logger.debug("Skipping locale update, `lang` unchanged", attribute);
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

    #host: ReactiveElementHost<LocaleMixin>;
    #context: ContextProvider<LocaleContext>;

    /**
     * @param host The host element.
     * @param localeHint The initial locale code to set.
     */
    constructor(
        host: ReactiveElementHost<LocaleMixin>,
        loaderInit?: LocaleLoaderInit,
        localeHint: Intl.UnicodeBCP47LocaleIdentifier = SourceLanguageTag,
    ) {
        this.#host = host;

        const loader = new LocaleLoader(loaderInit);
        this.sourceLocale = loader.sourceLocale;

        LocaleContextController.#localizationContext = configureLocalization(
            loader.toRuntimeConfig(),
        );

        this.#context = new ContextProvider(this.#host, {
            context: LocaleContext,
            initialValue: LocaleContextController.#localizationContext,
        });

        this.#host[kAKLocale] = LocaleContextController.#localizationContext;

        const nextLocale = localeHint || autoDetectLanguage();

        if (nextLocale !== this.sourceLocale) {
            this.#applyLocale(nextLocale);
        }
    }

    #localeStatusListener = (event: CustomEvent<LocaleStatusEventDetail>) => {
        if (event.detail.status === "error") {
            logger.debug("Error loading locale:", event.detail);
            return;
        }

        if (event.detail.status === "loading") {
            return;
        }

        const { readyLocale } = event.detail;
        logger.debug(`Updating \`lang\` attribute to: \`${readyLocale}\``);

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
