/**
 * @file Continuous-login multi-tab coordination.
 *
 * Continuous login (the `flows_continuous_login` feature flag) lets one authenticated tab resume
 * every other tab sitting in the same flow, so the user only enters credentials once. This suite
 * drives two real tabs in a single browser context — they share the BroadcastChannel, the Web Lock,
 * and the session cookie the orchestrator relies on — authenticates in the first, and asserts the
 * second completes on its own.
 *
 * ISOLATION: the flag is a GLOBAL instance setting, not per-brand, so enabling it perturbs the login
 * path for every concurrent test. This file therefore:
 *   - carries the highest numeric prefix, so it is ordered last, and
 *   - runs serially, enabling the flag in `beforeAll` and restoring it in `afterAll`.
 * In CI it should run in its own invocation, after the parallel suite. See ./AGENTS.md.
 */

import { expect, test } from "#e2e";
import { FormFixture } from "#e2e/fixtures/FormFixture";
import { NavigatorFixture } from "#e2e/fixtures/NavigatorFixture";
import { PointerFixture } from "#e2e/fixtures/PointerFixture";
import { SessionFixture } from "#e2e/fixtures/SessionFixture";

import type { Page } from "@playwright/test";

// The `/admin/settings` route mounted under the `/if/admin/` interface.
const SETTINGS_PATHNAME = "/if/admin/admin/settings";

const FLOW_PATHNAME = "/if/flow/default-authentication-flow/";
// Post-login destination shared by both tabs. Same-origin, so the follower resumes through
// FlowMultitabController's `next`-param branch rather than its own RedirectStage.
const USER_INTERFACE_PATHNAME = "/if/user/";
const FLOW_WITH_NEXT = `${FLOW_PATHNAME}?next=${encodeURIComponent(USER_INTERFACE_PATHNAME)}`;

const IDENTIFICATION_STAGE = "ak-stage-identification";

/**
 * Toggle the global Continuous Login flag through the admin settings UI.
 *
 * Runs from `beforeAll`/`afterAll`, where the per-test fixtures aren't injected,
 * so it constructs the handful it needs against a caller-supplied page and
 * drives the same UI a human would.
 *
 * The settings write is awaited so the flag is durable before the page closes.
 */
async function setContinuousLogin(page: Page, enabled: boolean): Promise<void> {
    const testName = "continuous-login-setup";
    const navigator = new NavigatorFixture(page, testName);
    const session = new SessionFixture({ page, testName, navigator });
    const form = new FormFixture(page, testName);
    const pointer = new PointerFixture({ page, testName });

    await session.login({ to: SETTINGS_PATHNAME });

    await form.setFormGroup(/Flags/, true);
    await form.setInputCheck("Continuous Login", enabled);

    await Promise.all([
        page.waitForResponse(
            (response) =>
                response.url().includes("/admin/settings/") &&
                ["PUT", "PATCH"].includes(response.request().method()) &&
                response.ok(),
        ),
        pointer.click("Save changes"),
    ]);
}

test.describe.configure({ mode: "serial" });

test.describe("Continuous login", () => {
    test.beforeAll(async ({ browser }) => {
        const page = await browser.newPage();

        await setContinuousLogin(page, true);
        await page.close();
    });

    test.afterAll(async ({ browser }) => {
        const page = await browser.newPage();

        await setContinuousLogin(page, false);
        await page.close();
    });

    test("resumes a pending tab once another tab authenticates", async ({
        context,
        page,
        session,
    }) => {
        // Two tabs in the same context: the leader (authenticates)
        // and the follower (waits to be resumed).
        // They share the BroadcastChannel and Web Lock the orchestrator coordinates over.
        const leader = page;
        const follower = await context.newPage();

        await test.step("Open both tabs on the identification stage", async () => {
            await leader.goto(FLOW_WITH_NEXT);
            await follower.goto(FLOW_WITH_NEXT);

            // The follower must be fully mounted before the leader completes,
            // or it won't answer the leader's tab-discovery broadcast and would never be resumed.
            await expect(
                leader.locator(IDENTIFICATION_STAGE),
                "Leader tab shows the identification stage",
            ).toBeVisible();
            await expect(
                follower.locator(IDENTIFICATION_STAGE),
                "Follower tab shows the identification stage",
            ).toBeVisible();
        });

        await test.step("Authenticate in the leader tab", async () => {
            // `session` is bound to `leader`; it's already on the flow pathname,
            // so login keeps the `?next=` and drives username/password in place.
            await session.login({ to: USER_INTERFACE_PATHNAME }, leader);
        });

        await test.step("Follower resumes without re-entering credentials", async () => {
            // The follower never had credentials entered.
            // Continuous login is the only thing that moves it off the identification stage.
            // With the flag off it would sit there.
            //
            // The leader's resume confirms the follower's departure via a timed fallback
            // before it navigates itself, so allow more than the default assertion budget here.

            await follower.waitForURL(`**${USER_INTERFACE_PATHNAME}**`, { timeout: 20_000 });

            await expect(
                follower.locator(IDENTIFICATION_STAGE),
                "Follower has left the identification stage",
            ).toBeHidden();
        });
    });
});
