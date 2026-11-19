import { localization } from "#common/ui/locale/runtime";

import { kAKLocale, LocaleContext, LocaleMixin } from "#elements/mixins/locale";
import type { ReactiveElementHost } from "#elements/types";

import { ContextProvider } from "@lit/context";

/**
 * Provides the page's localization runtime to descendants.
 *
 * @remarks
 *   The locale is loaded by {@linkcode initializeLocale} before the interface
 *   boots, and is fixed until the page reloads.
 */
export class LocaleContextController extends ContextProvider<LocaleContext> {
    constructor(host: ReactiveElementHost<LocaleMixin>) {
        super(host, {
            context: LocaleContext,
            initialValue: localization,
        });

        host[kAKLocale] = localization;
    }
}
