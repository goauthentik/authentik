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
        expect(plural(1, forms, "en")).toBe("one");
        expect(plural(0, forms, "en")).toBe("other");
        expect(plural(0, forms, "fr")).toBe("one");
        expect(plural(21, forms, "ru")).toBe("one");
        expect(plural(3, forms, "ru")).toBe("few");
        expect(plural(5, forms, "ru")).toBe("many");
    });

    it("falls back to the other form when a category is missing", () => {
        expect(plural(3, { one: () => "one", other: () => "other" }, "ru")).toBe("other");
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
