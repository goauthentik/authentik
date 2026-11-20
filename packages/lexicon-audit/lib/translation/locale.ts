//#region Parsing

const localeCache = new Map<string, Intl.Locale | null>();

/**
 * Parse a locale string with caching, accepting POSIX-style underscores.
 *
 * Adapted from `web/src/common/ui/locale/utils.ts`.
 */
export function safeParseLocale(candidate: string): Intl.Locale | null {
    if (localeCache.has(candidate)) {
        return localeCache.get(candidate)!;
    }

    let locale: Intl.Locale | null = null;

    try {
        locale = new Intl.Locale(candidate.trim().replaceAll("_", "-"));
    } catch {
        // Invalid locale string
    }

    localeCache.set(candidate, locale);

    return locale;
}

/**
 * Canonicalize a locale tag, accepting POSIX-style underscores.
 *
 * @returns The canonical BCP 47 tag, or `null` when the tag is invalid.
 */
export function canonicalizeLocale(tag: string): string | null {
    return safeParseLocale(tag)?.toString() ?? null;
}

//#endregion

//#region Lexicon matching

/**
 * Private-use regions for pseudo-locales, e.g. `en-XA`. They never match a lexicon.
 */
const PSEUDO_REGIONS = new Set(["XA", "XB"]);

export type LexiconMatch = "exact" | "likely" | "language" | "region-fallback";

export interface LexiconLocaleMatch {
    lexicon: string;
    match: LexiconMatch;
}

export interface LexiconMatchOptions {
    /**
     * Allow a lexicon for another region of the same language and script, e.g. `pt-PT` → `pt-BR`.
     */
    regionFallback?: boolean;
}

/**
 * Pick the lexicon for a translation locale.
 *
 * In order:
 *
 * 1. `exact`: the same tag.
 * 2. `likely`: the same language, script and region once both are maximized with CLDR likely subtags,
 *    e.g. `en` → `en-US`, `nb-Latn-NO` → `nb-NO`.
 * 3. `language`: a lexicon tagged with the language alone, e.g. `fr-CA` → `fr`.
 * 4. `region-fallback`, only when enabled: another region of the same language and script, the first
 *    in alphabetical order.
 */
export function matchLexiconLocale(
    tag: string,
    available: readonly string[],
    options: LexiconMatchOptions = {},
): LexiconLocaleMatch | null {
    const locale = safeParseLocale(tag);

    if (!locale || (locale.region && PSEUDO_REGIONS.has(locale.region))) {
        return null;
    }

    const canonical = locale.toString();

    if (available.includes(canonical)) {
        return { lexicon: canonical, match: "exact" };
    }

    const maximized = locale.maximize();
    const candidates = [...available]
        .sort()
        .map((lexicon) => ({ lexicon, parsed: safeParseLocale(lexicon) }))
        .filter(
            (candidate): candidate is { lexicon: string; parsed: Intl.Locale } =>
                candidate.parsed?.language === locale.language,
        );

    const sameScript = candidates.filter(
        ({ parsed }) => parsed.maximize().script === maximized.script,
    );

    const likely = sameScript.find(({ parsed }) => parsed.maximize().region === maximized.region);

    if (likely) {
        return { lexicon: likely.lexicon, match: "likely" };
    }

    const languageOnly = sameScript.find(({ parsed }) => !parsed.region);

    if (languageOnly) {
        return { lexicon: languageOnly.lexicon, match: "language" };
    }

    if (options.regionFallback && sameScript[0]) {
        return { lexicon: sameScript[0].lexicon, match: "region-fallback" };
    }

    return null;
}

//#endregion

//#region Scripts

/**
 * Scripts where a word can be one or two characters: Han, Japanese and Korean.
 */
const CJK_SCRIPTS = new Set(["Hani", "Hans", "Hant", "Jpan", "Kore"]);

/**
 * Whether a locale is written in a CJK script, inferring the script when it isn't given.
 */
export function isCJKLocale(tag: string): boolean {
    const script = safeParseLocale(tag)?.maximize().script;

    return Boolean(script && CJK_SCRIPTS.has(script));
}

//#endregion
