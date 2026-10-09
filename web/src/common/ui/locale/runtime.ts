/**
 * @remarks
 *   Lit Localize's own runtime (`configureLocalization`) never loads a module for the
 *   source locale, which would make it impossible to customize English messages
 *   with custom locale catalogs. This is otherwise a drop-in replacement for it.
 * @file Lit Localize runtime which also loads templates for the source locale.
 */

import {
    LOCALE_STATUS_EVENT,
    LocaleModule,
    LocaleStatusEventDetail,
    MsgFn,
    MsgOptions,
    TemplateLike,
} from "@lit/localize";
import { _installMsgImplementation } from "@lit/localize/init/install.js";
import { defaultMsg } from "@lit/localize/internal/default-msg.js";
import { Deferred } from "@lit/localize/internal/deferred.js";
import { generateMsgId } from "@lit/localize/internal/id-generation.js";
import { runtimeMsg } from "@lit/localize/internal/runtime-msg.js";

export interface RuntimeLocaleModule extends LocaleModule {
    /**
     * Templates taking precedence over {@linkcode LocaleModule.templates}, keyed by
     * message ID or by the ID generated from the source string, even for messages
     * with an explicit ID.
     */
    overrides?: LocaleModule["templates"];
}

export interface RuntimeConfiguration {
    sourceLocale: string;
    targetLocales: Iterable<string>;
    /**
     * Load the templates of a locale, including the source locale.
     */
    loadLocale: (locale: string) => Promise<RuntimeLocaleModule>;
}

export interface LocalizationRuntime {
    getLocale(): string;
    setLocale(locale: string): Promise<void>;
    /**
     * Load the active locale's templates again, e.g. after custom catalogs changed.
     */
    reloadLocale(): Promise<void>;
}

const sourceIDCache = new Map<string | TemplateStringsArray, string>();

/**
 * The ID Lit Localize generates for a message's source, regardless of an explicit ID.
 */
function sourceID(template: TemplateLike): string {
    const strings = typeof template === "string" ? template : template.strings;
    let id = sourceIDCache.get(strings);

    if (id === undefined) {
        id = generateMsgId(strings, typeof template !== "string" && !("strTag" in template));
        sourceIDCache.set(strings, id);
    }

    return id;
}

function dispatchStatusEvent(detail: LocaleStatusEventDetail) {
    window.dispatchEvent(new CustomEvent(LOCALE_STATUS_EVENT, { detail }));
}

export function configureLocalization({
    sourceLocale,
    targetLocales,
    loadLocale,
}: RuntimeConfiguration): LocalizationRuntime {
    const validLocales = new Set([sourceLocale, ...targetLocales]);

    let activeLocale = sourceLocale;
    let loadingLocale: string | undefined;
    let templates: LocaleModule["templates"] | undefined;
    let overrides: LocaleModule["templates"] | undefined;
    let loading = new Deferred<void>();
    let requestID = 0;

    loading.resolve();

    _installMsgImplementation(((template: TemplateLike, options?: MsgOptions) => {
        try {
            if (overrides) {
                const id = options?.id && options.id in overrides ? options.id : sourceID(template);

                if (id in overrides) {
                    return runtimeMsg(overrides, template, { ...options, id });
                }
            }

            return runtimeMsg(templates, template, options);
        } catch {
            // A custom translation with placeholders used for a message without expressions.
            return defaultMsg(template, options);
        }
    }) as MsgFn);

    const load = (nextLocale: string): Promise<void> => {
        if (!validLocales.has(nextLocale)) {
            throw new Error(`Invalid locale code: ${nextLocale}`);
        }

        const currentRequestID = ++requestID;

        loadingLocale = nextLocale;

        if (loading.settled) {
            loading = new Deferred();
        }

        dispatchStatusEvent({ status: "loading", loadingLocale: nextLocale });

        loadLocale(nextLocale).then(
            (module) => {
                // Another locale was requested in the meantime, which resolves the promise.
                if (currentRequestID !== requestID) return;

                activeLocale = nextLocale;
                loadingLocale = undefined;
                templates = module.templates;

                // Avoid looking up messages twice when there are no overrides
                overrides = Object.keys(module.overrides ?? {}).length
                    ? module.overrides
                    : undefined;

                dispatchStatusEvent({ status: "ready", readyLocale: nextLocale });
                loading.resolve();
            },
            (error: unknown) => {
                if (currentRequestID !== requestID) return;

                loadingLocale = undefined;

                dispatchStatusEvent({
                    status: "error",
                    errorLocale: nextLocale,
                    errorMessage: String(error),
                });

                loading.reject(error instanceof Error ? error : new Error(String(error)));
            },
        );

        return loading.promise;
    };

    return {
        getLocale: () => activeLocale,
        setLocale: (nextLocale) => {
            if (nextLocale === (loadingLocale ?? activeLocale)) {
                return loading.promise;
            }

            return load(nextLocale);
        },
        reloadLocale: () => load(loadingLocale ?? activeLocale),
    };
}
