import { expect, test } from "#e2e";
import { GOOD_PASSWORD, GOOD_USERNAME, SessionFixture } from "#e2e/fixtures/SessionFixture";

/**
 * Compatibility mode forces the ShadyDOM shim, so components render in the
 * light DOM instead of shadow roots. This uses a different render path and has
 * regressed before (#24968), so the login flow should be tested with it.
 *
 * `?compat` enables the shim for a single page load. We avoid enabling
 * `compatibility_mode` on the shared default authentication flow; see
 * `prerequisites.setup.ts` for why shared-flow changes do not belong in tests.
 */
const COMPAT_PATHNAME = `${SessionFixture.pathname}?compat`;

test.describe("Login in compatibility mode", () => {
    test("Authenticates through the ShadyDOM-rendered flow", async ({ session, page }) => {
        await test.step("Open the flow with the shim forced on", async () => {
            await page.goto(COMPAT_PATHNAME);

            await expect(
                page.locator('script[data-id="shady-dom"]'),
                "Server emits the ShadyDOM shim",
            ).toBeAttached();
        });

        await test.step("The polyfill takes over rendering", async () => {
            await expect(
                session.$identificationStage,
                "Identification stage renders",
            ).toBeVisible();

            const inUse = await page.evaluate(() => window.ShadyDOM?.inUse);

            expect(inUse, "ShadyDOM polyfill is driving the render").toBe(true);
        });

        await test.step("Authenticate", async () => {
            await session.login({
                username: GOOD_USERNAME,
                password: GOOD_PASSWORD,
                to: COMPAT_PATHNAME,
            });
        });

        await test.step("Lands on the user library", async () => {
            await expect(
                page.getByRole("heading", { level: 1 }),
                "Authenticated interface renders after the compatibility-mode login",
            ).toHaveText("Application Dashboard");
        });
    });
});

declare global {
    interface Window {
        ShadyDOM?: {
            /**
             * Flag indicating whether the ShadyDOM polyfill is currently in use.
             */
            inUse?: boolean;
        };
    }
}
