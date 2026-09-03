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
import { setInstanceFlag } from "#e2e/utils/settings";

const CONTINUOUS_LOGIN_FLAG = "Continuous Login";

const FLOW_PATHNAME = "/if/flow/default-authentication-flow/";
// Post-login destination shared by both tabs. Same-origin, so the follower resumes through
// FlowMultitabController's `next`-param branch rather than its own RedirectStage.
const USER_INTERFACE_PATHNAME = "/if/user/";
const FLOW_WITH_NEXT = `${FLOW_PATHNAME}?next=${encodeURIComponent(USER_INTERFACE_PATHNAME)}`;

const IDENTIFICATION_STAGE = "ak-stage-identification";

test.describe.configure({ mode: "serial" });

test.describe("Continuous login", () => {
    // `beforeAll`/`afterAll` rather than the usual per-test fixtures: the flag is global, so it is
    // toggled once for the file, and `afterAll` runs even when the test fails — restoring the flag
    // no matter the outcome, which a `test.step` or `afterEach` on the scenario can't guarantee.
    test.beforeAll(async ({ browser }) => {
        const page = await browser.newPage();

        await setInstanceFlag(page, CONTINUOUS_LOGIN_FLAG, true);
        await page.close();
    });

    test.afterAll(async ({ browser }) => {
        const page = await browser.newPage();

        await setInstanceFlag(page, CONTINUOUS_LOGIN_FLAG, false);
        await page.close();
    });

    test("resumes a pending tab once another tab authenticates", async ({
        context,
        page,
        session,
    }) => {
        // Two tabs in the same context: the leader (authenticates) and the follower (waits to be
        // resumed). They share the BroadcastChannel and Web Lock the orchestrator coordinates over.
        const leader = page;
        const follower = await context.newPage();

        await test.step("Open both tabs on the identification stage", async () => {
            await leader.goto(FLOW_WITH_NEXT);
            await follower.goto(FLOW_WITH_NEXT);

            // The follower must be fully mounted before the leader completes, or it won't answer
            // the leader's tab-discovery broadcast and would never be resumed.
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
            // `session` is bound to `leader`, already on the flow pathname, so login keeps the
            // `?next=` and drives username/password in place.
            await session.login({ to: USER_INTERFACE_PATHNAME });
        });

        await test.step("Follower resumes without re-entering credentials", async () => {
            // The follower never had credentials entered. Continuous login is the only thing that
            // moves it off the identification stage; with the flag off it would sit there.
            //
            // The leader's resume confirms the follower's departure via a timed fallback before it
            // navigates itself, so allow more than the default assertion budget here.
            await follower.waitForURL(`**${USER_INTERFACE_PATHNAME}**`, { timeout: 20_000 });

            await expect(
                follower.locator(IDENTIFICATION_STAGE),
                "Follower has left the identification stage",
            ).toBeHidden();
        });
    });
});
