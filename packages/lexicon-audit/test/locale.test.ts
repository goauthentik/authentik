import { canonicalizeLocale, isCJKLocale, matchLexiconLocale } from "#translation/locale";

import { describe, expect, it } from "vitest";

describe("canonicalizeLocale", () => {
    it("accepts underscores and canonicalizes case", () => {
        expect(canonicalizeLocale("en_us")).toBe("en-US");
        expect(canonicalizeLocale("zh_hans")).toBe("zh-Hans");
        expect(canonicalizeLocale("tok")).toBe("tok");
    });

    it("rejects invalid tags", () => {
        expect(canonicalizeLocale("not a locale")).toBeNull();
        expect(canonicalizeLocale("")).toBeNull();
    });
});

describe("matchLexiconLocale", () => {
    const available = ["en-GB", "en-US", "fr", "nb-NO", "pt-BR", "tok"];

    it("prefers an exact tag", () => {
        expect(matchLexiconLocale("en-GB", available)).toEqual({
            lexicon: "en-GB",
            match: "exact",
        });
        expect(matchLexiconLocale("tok", available)).toEqual({ lexicon: "tok", match: "exact" });
    });

    it("matches likely subtags", () => {
        expect(matchLexiconLocale("en", available)).toEqual({ lexicon: "en-US", match: "likely" });
        expect(matchLexiconLocale("nb-Latn-NO", available)).toEqual({
            lexicon: "nb-NO",
            match: "likely",
        });
    });

    it("falls back to a language-only lexicon", () => {
        expect(matchLexiconLocale("fr-CA", available)).toEqual({
            lexicon: "fr",
            match: "language",
        });
    });

    it("uses another region only when asked", () => {
        expect(matchLexiconLocale("pt-PT", available)).toBeNull();
        expect(matchLexiconLocale("pt-PT", available, { regionFallback: true })).toEqual({
            lexicon: "pt-BR",
            match: "region-fallback",
        });
    });

    it("never matches pseudo-locales or other scripts", () => {
        expect(matchLexiconLocale("en-XA", available, { regionFallback: true })).toBeNull();
        expect(matchLexiconLocale("sr-Cyrl", ["sr-Latn-RS"], { regionFallback: true })).toBeNull();
    });
});

describe("isCJKLocale", () => {
    it("infers the script when the tag omits it", () => {
        expect(["zh-TW", "zh-Hans", "ja", "ko-KR"].map(isCJKLocale)).toEqual([
            true,
            true,
            true,
            true,
        ]);
        expect(["en", "tok", "ru-RU", "sr-Cyrl"].map(isCJKLocale)).toEqual([
            false,
            false,
            false,
            false,
        ]);
    });
});
