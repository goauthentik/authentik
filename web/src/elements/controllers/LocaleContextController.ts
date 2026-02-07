import { sourceLocale, targetLocales } from "../../locale-codes.js";

import { LocaleLoaderRecord, TargetLanguageTag } from "#common/ui/locale/definitions";
import { formatDisplayName } from "#common/ui/locale/format";
import { autoDetectLanguage, isTargetLanguageTag } from "#common/ui/locale/utils";

import { kAKLocale, LocaleContext, LocaleContextValue, LocaleMixin } from "#elements/mixins/locale";
import type { ReactiveElementHost } from "#elements/types";

import { ConsoleLogger } from "#logger/browser";

import { ContextProvider } from "@lit/context";
import {
    configureLocalization,
    LOCALE_STATUS_EVENT,
    LocaleModule,
    LocaleStatusEventDetail,
} from "@lit/localize";
import type { ReactiveController } from "lit";

const logger = ConsoleLogger.prefix("controller/locale");

/**
 * Loads the locale module for the given locale code.
 *
 * @param locale The locale code to load.
 *
 * @remarks
 * This is used by `@lit/localize` to dynamically load locale modules,
 * as well synchronizing the document's `lang` attribute.
 */
function loadLocale(locale: string): Promise<LocaleModule> {
    const languageNames = new Intl.DisplayNames([locale, sourceLocale], {
        type: "language",
    });

    const displayName = formatDisplayName(locale, locale, languageNames);

    if (!isTargetLanguageTag(locale)) {
        // Lit localize ensures this function is only called with valid locales
        // but we add a runtime check nonetheless.

        throw new TypeError(`Unsupported locale code: ${locale} (${displayName})`);
    }

    logger.debug(`Loading "${displayName}" module...`);

    const loader = LocaleLoaderRecord[locale];

    return loader();
}

/**
 * A controller that provides the application configuration to the element.
 */
export class LocaleContextController implements ReactiveController {
    /**
     * A shared locale context value.
     */
    protected static context: LocaleContextValue = configureLocalization({
        sourceLocale,
        targetLocales,
        loadLocale,
    });

    protected static DocumentObserverInit: MutationObserverInit = {
        attributes: true,
        attributeFilter: ["lang"],
        attributeOldValue: true,
    };

    public get activeLanguageTag(): TargetLanguageTag {
        return LocaleContextController.context!.getLocale() as TargetLanguageTag;
    }

    public set activeLanguageTag(value: TargetLanguageTag) {
        LocaleContextController.context!.setLocale(value);
    }

    /**
     * Attempts to apply the given locale code.
     * @param nextLocale A user or agent preferred locale code.
     */
    #applyLocale(nextLocale: TargetLanguageTag) {
        const { activeLanguageTag } = this;

        const languageNames = new Intl.DisplayNames([nextLocale, sourceLocale], {
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
    constructor(host: ReactiveElementHost<LocaleContext>, localeHint?: TargetLanguageTag) {
        this.#host = host;

        this.#context = new ContextProvider(this.#host, {
            context: LocaleContext,
            initialValue: LocaleContextController.context,
        });

        this.#host[kAKLocale] = LocaleContextController.context;

        const nextLocale = localeHint || autoDetectLanguage();

        if (nextLocale !== sourceLocale) {
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
