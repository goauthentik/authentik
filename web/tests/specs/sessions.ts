import SessionPage, {
    BAD_PASSWORD,
    BAD_USERNAME,
    GOOD_PASSWORD,
    GOOD_USERNAME,
} from "#tests/pageobjects/session.page";
import UserLibraryPage from "#tests/pageobjects/user-library.page";
import { navigateBrowser } from "#tests/utils/navigation";
import { browser, expect } from "@wdio/globals";

describe("Session management", () => {
    afterEach(async () => {
        await SessionPage.logout();
        await navigateBrowser(SessionPage.pathname);
    });

    it("should login with valid credentials and reach the UserLibrary", async () => {
        await browser.pause(5000);
        await SessionPage.login({ username: GOOD_USERNAME, password: GOOD_PASSWORD });
        await expect(UserLibraryPage.$pageHeading).resolves.toHaveText("My applications");
    });

    it("fails on a bad username", async () => {
        await SessionPage.submitUsernameStage(BAD_USERNAME);
        await SessionPage.submitPasswordStage(GOOD_PASSWORD);

        await expect(SessionPage.$authFailureMessage).resolves.toBeDisplayedInViewport();
        await expect(SessionPage.$authFailureMessage).resolves.toHaveText("Invalid password");
    });

    it("fails on a bad password", async () => {
        await SessionPage.submitUsernameStage(GOOD_USERNAME);
        await SessionPage.submitPasswordStage(BAD_PASSWORD);

        await expect(SessionPage.$authFailureMessage).resolves.toBeDisplayedInViewport();
        await expect(SessionPage.$authFailureMessage).resolves.toHaveText("Invalid password");
    });
});
