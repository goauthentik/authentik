import { MessageFormatter } from "#common/ui/locale/format";
import { withPluralCategory } from "#common/ui/locale/plural-category";

/**
 * Formats one plural variant. Receives the count, formatted for the active locale.
 */
export type PluralFormatter = MessageFormatter<string, [count: string]>;

/**
 * The variants of a pluralized message, modeled on the variants of an MF2
 * `.match {$count :number}` message.
 *
 * Numeric keys match a count exactly and take priority over categories, like MF2's `0 {{…}}`.
 *
 * The other keys are CLDR plural categories, not literal numbers. In Russian, "one" also covers 21
 * and 31, and in French it covers 0, so every category form must interpolate the count.
 *
 * @see {@link https://github.com/unicode-org/message-format-wg/blob/main/spec/functions/number.md MF2 :number}
 * @see {@link https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/PluralRules MDN}
 */
export type PluralForms = {
    /**
     * Required fallback for any count no other key matches, like MF2's `*` variant.
     */
    other: PluralFormatter;
} & Partial<Record<Exclude<Intl.LDMLPluralRule, "other">, PluralFormatter>> & {
        [exact: number]: PluralFormatter;
    };

/**
 * Options for {@linkcode plural}, named as in {@linkcode Intl.PluralRules}.
 *
 * Digit options affect both the formatted count and the selected category, as in MF2, where
 * "1.0" selects "other" in English.
 */
export interface PluralOptions extends Intl.PluralRulesOptions {
    /**
     * The locale to select and format with. Defaults to the active translation's locale.
     */
    locale?: Intl.LocalesArgument;
}

/**
 * The active translation's locale, read from the document's `lang` attribute, which the locale
 * controller keeps in sync. It can differ from the browser's own locale.
 *
 * Anything can write the attribute, a browser extension included, so a tag that is not valid falls
 * back to the runtime default instead of making every pluralized message throw.
 */
function documentLocale(): string | undefined {
    const lang = globalThis.document?.documentElement.lang;

    if (!lang) return undefined;

    try {
        return Intl.getCanonicalLocales(lang)[0];
    } catch {
        return undefined;
    }
}

const PluralRulesCache = new Map<string, Intl.PluralRules>();
const NumberFormatCache = new Map<string, Intl.NumberFormat>();

/**
 * Get a cached Intl formatter for the given locale and options.
 */
function cached<T>(
    cache: Map<string, T>,
    locale: Intl.LocalesArgument,
    options: Intl.PluralRulesOptions,
    create: () => T,
): T {
    const key = JSON.stringify([String(locale ?? ""), options]);
    let instance = cache.get(key);

    if (!instance) {
        instance = create();
        cache.set(key, instance);
    }

    return instance;
}

/**
 * Select and format the variant of a pluralized message for a count, like an MF2
 * `.match {$count :number}` message.
 *
 * An exact numeric key wins over the count's plural category. A category the forms leave out
 * formats with the "other" form, using the locale's translation for that category when the
 * catalog has one.
 *
 * @param count The count to select by.
 * @param forms The message variants.
 * @param options Locale and {@linkcode Intl.PluralRules} options.
 */
export function plural(count: number, forms: PluralForms, options: PluralOptions = {}): string {
    const { locale: explicitLocale, ...ruleOptions } = options;
    const locale = explicitLocale ?? documentLocale();

    const rules = cached(PluralRulesCache, locale, ruleOptions, () => {
        return new Intl.PluralRules(locale, ruleOptions);
    });

    const { type: _type, ...numberOptions } = ruleOptions;

    const numberFormat = cached(NumberFormatCache, locale, numberOptions, () => {
        return new Intl.NumberFormat(locale, numberOptions);
    });

    const formattedCount = numberFormat.format(count);
    const exact = forms[count];

    if (exact) return exact(formattedCount);

    const category = rules.select(count);
    const formatter = forms[category] ?? forms.other;

    return withPluralCategory(category, () => formatter(formattedCount));
}
