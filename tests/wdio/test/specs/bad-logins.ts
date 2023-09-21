import { expect } from "@wdio/globals";
import LoginPage from "../pageobjects/login.page.js";
import UserLibraryPage from "../pageobjects/user-library.page.js";

describe("Log into Authentik", () => {
    it("should fail on a bad username", async () => {
        await LoginPage.open();
        await LoginPage.username("bad-username@bad-logio.io");
        const failure = await LoginPage.authFailure;
        expect(failure).toHaveText("Failed to authenticate.");
    });

    it("should fail on a bad password", async () => {
        await LoginPage.open();
        await LoginPage.username("ken@goauthentik.io");
        await LoginPage.pause();
        await LoginPage.password("-this-is-a-bad-password-");
        const failure = await LoginPage.authFailure;
        expect(failure).toHaveText("Failed to authenticate.");
    });
});
