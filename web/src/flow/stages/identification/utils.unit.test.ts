import { createOrListFormatter } from "#flow/stages/identification/utils";

import { describe, expect, it } from "vitest";

describe("createOrListFormatter", () => {
    it("localizes the disjunction word for the given locale", () => {
        expect(createOrListFormatter("en-US").format(["Email", "Username"])).toBe(
            "Email or Username",
        );
        expect(createOrListFormatter("cs-CZ").format(["E-mail", "Uživatelské jméno"])).toBe(
            "E-mail nebo Uživatelské jméno",
        );
        expect(createOrListFormatter("de-DE").format(["E-Mail", "Anmeldename"])).toBe(
            "E-Mail oder Anmeldename",
        );
    });

    it("does not fall back to the runtime's own default locale", () => {
        // Guards against reintroducing the hardcoded "default" locale.
        const formatted = createOrListFormatter("cs-CZ").format(["E-mail", "Uživatelské jméno"]);

        expect(formatted).not.toContain(" or ");
    });
});
