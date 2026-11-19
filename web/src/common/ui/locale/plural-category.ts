/**
 * @remarks
 *   Source code writes only the forms English needs. A locale with more
 *   categories has a translation for each, under `<base>.<category>`. While
 *   {@linkcode plural} formats a form, lookups of any `<base>.<category>` id
 *   resolve to the selected category's translation when the catalog has one.
 *   Keep this module free of `msg()` calls: the locale runtime imports it.
 * @file Redirects a plural form's catalog lookup to the selected category.
 */

import type { LocaleModule } from "@lit/localize";

const CategoryIDPattern = /^(.+)\.(?:zero|one|two|few|many|other)$/;

let activeCategory: Intl.LDMLPluralRule | null = null;

/**
 * Run a formatter with catalog lookups redirected to the given category.
 */
export function withPluralCategory<T>(category: Intl.LDMLPluralRule, formatter: () => T): T {
    const previous = activeCategory;
    activeCategory = category;

    try {
        return formatter();
    } finally {
        activeCategory = previous;
    }
}

/**
 * Wrap a locale catalog so plural form lookups follow the active category.
 */
export function withPluralRedirect(module: LocaleModule): LocaleModule {
    const templates = new Proxy(module.templates, {
        get(target, id, receiver) {
            if (activeCategory && typeof id === "string") {
                const base = CategoryIDPattern.exec(id)?.[1];
                const redirected = base ? target[`${base}.${activeCategory}`] : undefined;

                if (redirected) return redirected;
            }

            return Reflect.get(target, id, receiver);
        },
    });

    return { ...module, templates };
}
