import LoginPage from "../pageobjects/login.page.js";
import UserLibraryPage from "../pageobjects/user-library.page.js";
import { expect } from "@wdio/globals";

describe("Log into Authentik", () => {
    it("should login with valid credentials", async () => {
        await LoginPage.open();
        await LoginPage.login("ken@goauthentik.io", "eat10bugs");
        await expect(UserLibraryPage.pageHeader).toHaveText("My applications");
    });
});
