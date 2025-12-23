/**
 * @file Han Script utilities
 */

import { UnwrapSet } from "#common/sets";
import { TargetLanguageTag } from "#common/ui/locale/definitions";

//#region Constants

/**
 * An enum-like record of language tag constants that require special handling.
 */
export const CJKLanguageTag = {
    HanSimplified: "zh-Hans",
    HanTraditional: "zh-Hant",
    Japanese: "ja-JP",
    Korean: "ko-KR",
} as const satisfies Record<string, TargetLanguageTag>;

export type CJKLanguageTag = (typeof CJKLanguageTag)[keyof typeof CJKLanguageTag];

/**
 * A set of **supported language tags** representing languages using Han scripts, i.e. Chinese.
 */
export const HanLanguageTags = new Set([
    CJKLanguageTag.HanSimplified,
    CJKLanguageTag.HanTraditional,
] as const satisfies TargetLanguageTag[]);

export type HanLanguageTag = UnwrapSet<typeof HanLanguageTags>;

/**
 * A set of **supported language tags** representing Chinese, Japanese, and Korean languages.
 */
export const CJKLanguageTags = new Set<CJKLanguageTag>(Object.values(CJKLanguageTag));

//#endregion

export const HanScriptTag = {
    Simplified: "Hans",
    Traditional: "Hant",
} as const satisfies Record<string, string>;

export type HanScriptTag = (typeof HanScriptTag)[keyof typeof HanScriptTag];

/**
 * Mapping of regions to their conventional script for Chinese.
 *
 * Covers major regions; others fall back to CLDR via `Intl.Locale.maximize`.
 */
export const ZHRegionToHanScript: ReadonlyMap<string, HanScriptTag> = new Map([
    ["TW", HanScriptTag.Traditional], // Taiwan
    ["HK", HanScriptTag.Traditional], // Hong Kong
    ["MO", HanScriptTag.Traditional], // Macau
    ["CN", HanScriptTag.Simplified], // China
    ["SG", HanScriptTag.Simplified], // Singapore
    ["MY", HanScriptTag.Simplified], // Malaysia
]);

/**
 * Resolve a Chinese locale to it's preferred script tag.
 *
 * Priority:
 * 1. Explicit script subtag (zh-Hant, zh-Hans)
 * 2. Known region mapping (TW, HK, CN, etc.)
 * 3. CLDR maximize() inference
 * 4. Fallback to Simplified (Hans)
 *
 * @see {@linkcode resolveChineseScriptLegacy} for a regex-based approach.
 */
export function resolveChineseScript(locale: Intl.Locale): HanScriptTag {
    if (locale.script === HanScriptTag.Traditional || locale.script === HanScriptTag.Simplified) {
        return locale.script;
    }

    const scriptViaRegion = locale.region ? ZHRegionToHanScript.get(locale.region) : null;

    if (scriptViaRegion) {
        return scriptViaRegion;
    }

    try {
        const maximized = locale.maximize();

        if (
            maximized.script === HanScriptTag.Traditional ||
            maximized.script === HanScriptTag.Simplified
        ) {
            return maximized.script;
        }
    } catch (_error) {
        // maximize() not supported or failed
    }

    return HanScriptTag.Simplified;
}

/**
 * Resolve Chinese locale fallback to either zh-Hans or zh-Hant.
 */
export function resolveChineseFallback(
    candidate: string,
): typeof CJKLanguageTag.HanSimplified | typeof CJKLanguageTag.HanTraditional {
    // Explicit script?
    if (/[-_]hant\b/i.test(candidate)) return CJKLanguageTag.HanTraditional;
    if (/[-_]hans\b/i.test(candidate)) return CJKLanguageTag.HanSimplified;

    // Traditional region?
    if (/[-_](tw|hk|mo)\b/i.test(candidate)) return CJKLanguageTag.HanTraditional;

    return CJKLanguageTag.HanSimplified;
}

/**
 * Resolve Chinese script using a regex-based approach for browser compatibility.
 *
 * @see {@linkcode resolveChineseScript} to resolve from {@linkcode Intl.Locale}
 */
export function resolveChineseScriptLegacy(candidate: string): HanScriptTag {
    // Explicit script?
    if (/[-_]hant\b/i.test(candidate)) return HanScriptTag.Traditional;
    if (/[-_]hans\b/i.test(candidate)) return HanScriptTag.Simplified;

    // Traditional region?
    if (/[-_](tw|hk|mo)\b/i.test(candidate)) return HanScriptTag.Traditional;

    return HanScriptTag.Simplified;
}

//#region Type Guards

export function isCJKLanguageTag(languageTag: string): languageTag is CJKLanguageTag {
    return CJKLanguageTags.has(languageTag as CJKLanguageTag);
}

export function isHanLanguageTag(languageTag: string): languageTag is HanLanguageTag {
    return HanLanguageTags.has(languageTag as HanLanguageTag);
}

//#endregion
