import { expect, test } from "#e2e";
import {
    BAD_PASSWORD,
    BAD_USERNAME,
    GOOD_PASSWORD,
    GOOD_USERNAME,
} from "#e2e/fixtures/SessionFixture";

test.beforeEach(async ({ session }) => {
    await session.toLoginPage();
});

test.describe("Session management", () => {
    test("Login with valid credentials", async ({ session, page }) => {
        await session.login({ username: GOOD_USERNAME, password: GOOD_PASSWORD });

        await expect(
            page.getByRole("heading", {
                level: 1,
            }),
        ).toHaveText("My applications");
    });

    test("Reject bad username", async ({ session }) => {
        await session.login({ username: BAD_USERNAME, password: GOOD_PASSWORD });

        await expect(session.$authFailureMessage).toBeVisible();
    });

    test("Reject bad password", async ({ session }) => {
        await session.login({ username: GOOD_USERNAME, password: BAD_PASSWORD });

        await expect(session.$authFailureMessage).toBeVisible();
    });
});
