import { expect, test } from "#e2e";
import { GOOD_PASSWORD, GOOD_USERNAME, SessionFixture } from "#e2e/fixtures/SessionFixture";

/**
 * Compatibility mode serves the flow with the ShadyDOM shim forced on, which
 * renders every component into the light DOM instead of a shadow root. It is a
 * genuinely different rendering path — nested CSS was silently dropped there
 * once (#24968), taking the login layout with it — so the login flow is worth
 * exercising through it.
 *
 * `?compat` forces the shim for one page load. The alternative is switching
 * `compatibility_mode` on the default authentication flow, which every worker
 * in this suite authenticates through, and `prerequisites.setup.ts` explains
 * why that kind of shared-flow edit does not belong in a test.
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

            // `ShadyDOM.inUse` is the only honest signal here. The `force` flag the
            // shim sets is consumed during initialization, and a polyfilled root
            // still reports `instanceof ShadowRoot` — neither distinguishes this
            // path from an ordinary render.
            const inUse = await page.evaluate(
                () => (window as unknown as { ShadyDOM?: { inUse?: boolean } }).ShadyDOM?.inUse,
            );

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
