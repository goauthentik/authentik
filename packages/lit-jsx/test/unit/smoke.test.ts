import { PACKAGE_NAME } from "@goauthentik/lit-jsx";

import { expect, it } from "vitest";

it("resolves the package from source via the vitest alias", () => {
    expect(PACKAGE_NAME).toBe("@goauthentik/lit-jsx");
});
