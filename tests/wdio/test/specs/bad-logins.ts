import LoginPage from "../pageobjects/login.page.js";
import { BAD_PASSWORD, BAD_USERNAME, GOOD_USERNAME } from "../utils/constants.js";
import { expect } from "@wdio/globals";

describe("Log into authentik", () => {
    it("should fail on a bad username", async () => {
        await LoginPage.open();
        await LoginPage.username(BAD_USERNAME);
        const failure = await LoginPage.authFailure;
        expect(failure).toHaveText("Failed to authenticate.");
    });

    it("should fail on a bad password", async () => {
        await LoginPage.open();
        await LoginPage.username(GOOD_USERNAME);
        await LoginPage.pause();
        await LoginPage.password(BAD_PASSWORD);
        const failure = await LoginPage.authFailure;
        expect(failure).toHaveText("Failed to authenticate.");
    });
});
