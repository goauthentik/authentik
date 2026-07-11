import { jsx } from "@goauthentik/lit-jsx";

import { expect, it } from "vitest";

it("resolves the package from source via the vitest alias", () => {
    expect(typeof jsx).toBe("function");
});
