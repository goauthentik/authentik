import { expect } from "@wdio/globals";

import LoginPage from "../pageobjects/login.page.js";
import { BAD_USERNAME, GOOD_PASSWORD } from "../utils/constants.js";

describe("Log into authentik", () => {
    it("should fail on a bad username", async () => {
        await LoginPage.open();
        await LoginPage.username(BAD_USERNAME);
        await LoginPage.pause();
        await LoginPage.password(GOOD_PASSWORD);
        const failure = await LoginPage.authFailure();
        await expect(failure).toBeDisplayedInViewport();
        await expect(failure).toHaveText("Invalid password");
    });
});
