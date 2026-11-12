import { withPluralRedirect } from "#common/ui/locale/plural-category";
import { plural } from "#common/ui/locale/plurals";

import { beforeAll, describe, expect, it } from "vitest";

import { configureLocalization, msg, str } from "@lit/localize";

const attempts = (count: number) =>
    plural(
        count,
        {
            one: (formattedCount) =>
                msg(str`${formattedCount} attempt`, { id: "test.attempts.one" }),
            other: (formattedCount) =>
                msg(str`${formattedCount} attempts`, { id: "test.attempts.other" }),
        },
        { locale: "ru" },
    );

describe("plural forms in a translated catalog", () => {
    beforeAll(async () => {
        const { setLocale } = configureLocalization({
            sourceLocale: "en",
            targetLocales: ["ru"],
            loadLocale: () =>
                Promise.resolve(
                    withPluralRedirect({
                        templates: {
                            "test.attempts.one": str`${0} попытка`,
                            "test.attempts.few": str`${0} попытки`,
                            "test.attempts.many": str`${0} попыток`,
                            "test.attempts.other": str`${0} попытки`,
                        },
                    }),
                ),
        });

        await setLocale("ru");
    });

    it("uses the translation for categories the source does not write", () => {
        expect(attempts(1)).toBe("1 попытка");
        expect(attempts(3)).toBe("3 попытки");
        expect(attempts(5)).toBe("5 попыток");
        expect(attempts(1.5)).toBe("1,5 попытки");
    });

    it("does not redirect lookups outside plural()", () => {
        const count = 3;

        expect(msg(str`${count} attempts`, { id: "test.attempts.other" })).toBe("3 попытки");
        expect(msg(str`${count} attempt`, { id: "test.attempts.one" })).toBe("3 попытка");
    });
});
