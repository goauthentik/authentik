import { expect } from "@wdio/globals";

import LoginPage from "../pageobjects/login.page.js";
import { BAD_PASSWORD, GOOD_USERNAME } from "../utils/constants.js";

describe("Log into authentik", () => {
    it("should fail on a bad password", async () => {
        await LoginPage.open();
        await LoginPage.username(GOOD_USERNAME);
        await LoginPage.pause();
        await LoginPage.password(BAD_PASSWORD);
        const failure = await LoginPage.authFailure();
        await expect(failure).toBeDisplayedInViewport();
        await expect(failure).toHaveText("Invalid password");
    });
});
