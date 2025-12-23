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
export const CJKLanguageTags: Set<CJKLanguageTag> = new Set(Object.values(CJKLanguageTag));

//#endregion

export const HanScriptTag = {
    Simplified: "Hans",
    Traditional: "Hant",
} as const satisfies Record<string, string>;

export type HanScriptTag = (typeof HanScriptTag)[keyof typeof HanScriptTag];

/**
 * Mapping of regions to their conventional script for Chinese.
 * Covers major regions; others fall back to CLDR via maximize().
 */
export const ZH_REGION_TO_SCRIPT = new Map<string, HanScriptTag>([
    ["TW", HanScriptTag.Traditional],
    ["HK", HanScriptTag.Traditional],
    ["MO", HanScriptTag.Traditional],
    ["CN", HanScriptTag.Simplified],
    ["SG", HanScriptTag.Simplified],
    ["MY", HanScriptTag.Simplified],
]);

/**
 * Resolve a Chinese locale to either zh-Hans or zh-Hant.
 *
 * Priority:
 * 1. Explicit script subtag (zh-Hant, zh-Hans)
 * 2. Known region mapping (TW, HK, CN, etc.)
 * 3. CLDR maximize() inference
 * 4. Fallback to Simplified (Hans)
 */
export function resolveChineseScript(locale: Intl.Locale): HanScriptTag {
    if (locale.script === HanScriptTag.Traditional || locale.script === HanScriptTag.Simplified) {
        return locale.script;
    }

    const scriptViaRegion = locale.region ? ZH_REGION_TO_SCRIPT.get(locale.region) : null;
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
    } catch {
        // maximize() not supported or failed
    }

    return HanScriptTag.Simplified;
}

export function resolveChineseFallback(candidate: string): "zh-Hans" | "zh-Hant" {
    // Check for explicit script
    if (/[-_]hant\b/i.test(candidate)) return "zh-Hant";
    if (/[-_]hans\b/i.test(candidate)) return "zh-Hans";

    // Check for Traditional regions
    if (/[-_](tw|hk|mo)\b/i.test(candidate)) return "zh-Hant";

    // Default to Simplified
    return "zh-Hans";
}

/**
 * Resolve Chinese script for browsers without good Intl.Locale support.
 */
export function resolveChineseScriptFallback(candidate: string): HanScriptTag {
    // Is there an explicit script subtag?
    if (/[-_]hant\b/i.test(candidate)) return HanScriptTag.Traditional;
    if (/[-_]hans\b/i.test(candidate)) return HanScriptTag.Simplified;

    // Does the region imply Traditional?
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
