/**
 * Defines the plural forms for a given locale, and provides a function to select the appropriate form based on a count.
 *
 * @see {@link https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/PluralRules MDN} for more information on plural categories and rules.
 */
export interface PluralForms {
    /**
     * The "other" form is required as a fallback for categories that may not be provided.
     * For example, if only "one" and "other" are provided,
     * then "other" will be used for all counts that don't fall into the "one" category.
     */
    other: () => string;
    /**
     * Used for counts that fall into the "one" category for the given locale.
     */
    one?: () => string;
    /**
     * Used for counts that fall into the "two" category for the given locale.
     */
    two?: () => string;
    /**
     * Used for counts that fall into the "few" category for the given locale.
     */
    few?: () => string;
    /**
     * Used for counts that fall into the "many" category for the given locale.
     */
    many?: () => string;
    /**
     * Used for counts that fall into the "zero" category for the given locale.
     */
    zero?: () => string;
}

/**
 * Cache of {@linkcode Intl.PluralRules} instances, keyed by locale argument. The empty string key is used for the default locale.
 */
const PluralRulesCache = new Map<Intl.LocalesArgument, Intl.PluralRules>();

/**
 * Get an {@linkcode Intl.PluralRules} instance for the given locale, using a cache to avoid unnecessary allocations.
 *
 * @param locale The locale to get plural rules for, or undefined to use the default locale.
 * @returns An {@linkcode Intl.PluralRules} instance for the given locale.
 */
function getPluralRules(locale?: Intl.LocalesArgument): Intl.PluralRules {
    const key = locale ?? "";
    let pr = PluralRulesCache.get(key);

    if (!pr) {
        pr = new Intl.PluralRules(locale);
        PluralRulesCache.set(key, pr);
    }
    return pr;
}

/**
 * Get the appropriate plural form for a given count and set of forms.
 *
 * @param count The count to get the plural form for.
 * @param forms The forms to use for each plural category.
 * @param locale The locale to use for determining the plural category, or undefined to use the default locale.
 */
export function plural(count: number, forms: PluralForms, locale?: Intl.LocalesArgument): string {
    const category = getPluralRules(locale).select(count);

    return (forms[category] ?? forms.other)();
}
