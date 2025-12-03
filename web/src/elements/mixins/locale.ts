import { TargetLocale } from "#common/ui/locale/definitions";

import { createMixin } from "#elements/types";

import { consume, createContext } from "@lit/context";
import type { configureLocalization } from "@lit/localize";

export type LocaleContextValue = ReturnType<typeof configureLocalization>;

export const kAKLocale = Symbol("kAKLocale");

/**
 * The Lit context for the application configuration.
 *
 * @category Context
 * @see {@linkcode LocaleMixin}
 * @see {@linkcode WithLocale}
 */
export const LocaleContext = createContext<LocaleContextValue>(
    Symbol.for("authentik-locale-context"),
);

export type LocaleContext = typeof LocaleContext;

/**
 * A consumer that provides session information to the element.
 *
 * @category Mixin
 * @see {@linkcode WithLocale}
 */
export interface LocaleMixin {
    /**
     * The locale context value.
     *
     * @internal
     */
    readonly [kAKLocale]: Readonly<LocaleContextValue>;

    /**
     * The current locale code.
     */
    locale: TargetLocale;
}

/**
 * A mixin that provides locale information to the element.
 *
 * @category Mixin
 */
export const WithLocale = createMixin<LocaleMixin>(
    ({
        // ---
        SuperClass,
        subscribe = true,
    }) => {
        abstract class LocaleProvider extends SuperClass implements LocaleMixin {
            @consume({
                context: LocaleContext,
                subscribe,
            })
            public [kAKLocale]!: LocaleContextValue;

            public get locale(): TargetLocale {
                return this[kAKLocale].getLocale() as TargetLocale;
            }

            public set locale(value: TargetLocale) {
                this[kAKLocale].setLocale(value);
            }
        }

        return LocaleProvider;
    },
);
