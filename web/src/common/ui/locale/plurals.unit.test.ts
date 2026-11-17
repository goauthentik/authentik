import { plural, type PluralForms } from "#common/ui/locale/plurals";

import { afterEach, describe, expect, it } from "vitest";

const forms: PluralForms = {
    one: () => "one",
    few: () => "few",
    many: () => "many",
    other: () => "other",
};

describe("plural", () => {
    afterEach(() => {
        Reflect.deleteProperty(globalThis, "document");
    });

    it("selects by CLDR category, not by literal count", () => {
        expect(plural(1, forms, { locale: "en" })).toBe("one");
        expect(plural(0, forms, { locale: "en" })).toBe("other");
        expect(plural(0, forms, { locale: "fr" })).toBe("one");
        expect(plural(21, forms, { locale: "ru" })).toBe("one");
        expect(plural(3, forms, { locale: "ru" })).toBe("few");
        expect(plural(5, forms, { locale: "ru" })).toBe("many");
    });

    it("falls back to the other form when a category is missing", () => {
        expect(plural(3, { one: () => "one", other: () => "other" }, { locale: "ru" })).toBe(
            "other",
        );
    });

    it("prefers an exact count over the plural category", () => {
        const withZero: PluralForms = { ...forms, 0: () => "none" };

        expect(plural(0, withZero, { locale: "en" })).toBe("none");
        expect(plural(0, withZero, { locale: "fr" })).toBe("none");
        expect(plural(1, withZero, { locale: "en" })).toBe("one");
    });

    it("passes the count formatted for the locale", () => {
        const echo: PluralForms = { other: (count) => count };

        expect(plural(1234, echo, { locale: "en" })).toBe("1,234");
        expect(plural(1234, echo, { locale: "de" })).toBe("1.234");
    });

    it("applies digit options to both selection and formatting", () => {
        const echo: PluralForms = {
            one: (count) => `one ${count}`,
            other: (count) => `other ${count}`,
        };

        expect(plural(1, echo, { locale: "en", minimumFractionDigits: 1 })).toBe("other 1.0");
    });

    it("selects ordinal categories", () => {
        const ordinal: PluralForms = {
            one: () => "st",
            two: () => "nd",
            few: () => "rd",
            other: () => "th",
        };

        expect(plural(22, ordinal, { locale: "en", type: "ordinal" })).toBe("nd");
        expect(plural(13, ordinal, { locale: "en", type: "ordinal" })).toBe("th");
    });

    it("defaults to the document's language, not the runtime's", () => {
        Object.defineProperty(globalThis, "document", {
            configurable: true,
            value: { documentElement: { lang: "ru-RU" } },
        });

        expect(plural(21, forms)).toBe("one");
        expect(plural(11, forms)).toBe("many");
    });

    it("ignores a document language that is not a valid tag", () => {
        Object.defineProperty(globalThis, "document", {
            configurable: true,
            value: { documentElement: { lang: "en_US" } },
        });

        expect(() => plural(1, forms)).not.toThrow();
    });
});
