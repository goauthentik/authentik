import { expect, test } from "#e2e";
import { BAD_PASSWORD, BAD_USERNAME, GOOD_PASSWORD, GOOD_USERNAME } from "#e2e/fixtures/session";

test.beforeEach(async ({ session }) => {
    await session.toLoginPage();
});

test.describe("Session management", () => {
    test("Login with valid credentials", async ({ session, userLibrary }) => {
        await session.login({ username: GOOD_USERNAME, password: GOOD_PASSWORD });

        await expect(userLibrary.$pageHeading).toHaveText("My applications");
    });

    test("Reject bad username", async ({ session }) => {
        await session.submitUsernameStage(BAD_USERNAME);
        await session.submitPasswordStage(GOOD_PASSWORD);

        await expect(session.$authFailureMessage).toBeVisible();
        await expect(session.$authFailureMessage).toHaveText("Invalid password");
    });

    test("Reject bad password", async ({ session }) => {
        await session.submitUsernameStage(GOOD_USERNAME);
        await session.submitPasswordStage(BAD_PASSWORD);

        await expect(session.$authFailureMessage).toBeVisible();
        await expect(session.$authFailureMessage).toHaveText("Invalid password");
    });
});
