/**
 * @file Tests continuous login across two browser tabs. With `flows_continuous_login` enabled, one
 *   tab can resume another tab in the same flow. The user enters credentials once. This test
 *   authenticates in one tab and checks that the other completes. Both tabs share a
 *   BroadcastChannel, Web Lock, and session cookie. **Isolation:** This is a global instance
 *   setting, so enabling it affects concurrent tests.
 *
 *   - Serial execution enables the flag in `beforeAll` and restores it in `afterAll`.
 *   - In CI, run this file separately, after the parallel suite. See `./AGENTS.md`.
 */

import { expect, test } from "#e2e";
import { setInstanceFlag } from "#e2e/utils/settings";

import type { Page } from "@playwright/test";

const CONTINUOUS_LOGIN_FLAG = "Continuous Login";

const FLOW_PATHNAME = "/if/flow/default-authentication-flow/";
// Post-login destination shared by both tabs. Same-origin, so the follower resumes through
// FlowMultitabController's `next`-param branch rather than its own RedirectStage.
const USER_INTERFACE_PATHNAME = "/if/user/";
const FLOW_WITH_NEXT = `${FLOW_PATHNAME}?next=${encodeURIComponent(USER_INTERFACE_PATHNAME)}`;

const IDENTIFICATION_STAGE = "ak-stage-identification";

// Seeded by `test/blueprints/test-continuous-login-source.yaml`: a single unreachable source and
// no user fields, so the identification stage redirects to the source on its own.
const SOURCE_FLOW_WITH_NEXT = `/if/flow/test-continuous-login-source/?next=${encodeURIComponent(USER_INTERFACE_PATHNAME)}`;

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
            // System settings are cached per server process, so a tab may render with the flag
            // still off for a while after it's saved. Reload until each tab sees it.
            for (const tab of [leader, follower]) {
                await expect(async () => {
                    await tab.goto(FLOW_WITH_NEXT);

                    const flags = await tab.evaluate(
                        () =>
                            JSON.parse(document.getElementById("ak-brand")?.textContent ?? "{}")
                                .flags,
                    );

                    expect(flags?.flows_continuous_login).toBe(true);
                }, "Tab renders with continuous login enabled").toPass({ timeout: 35_000 });
            }

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

    test("sends only one tab to a single auto-redirecting source", async ({
        baseURL,
        context,
        page,
        session,
    }) => {
        const tabs = await test.step("Open three tabs on the source flow at once", async () => {
            let opened: Page[] = [];

            // System settings are cached per server process, so retry until every tab was
            // rendered with the flag on.
            await expect(async () => {
                await Promise.all(opened.map((tab) => tab.close()));

                opened = await Promise.all([0, 1, 2].map(() => context.newPage()));

                const responses = await Promise.all(
                    opened.map((tab) => tab.goto(SOURCE_FLOW_WITH_NEXT)),
                );

                for (const response of responses) {
                    expect(await response?.text()).toMatch(/"flows_continuous_login":\s*true/);
                }
            }, "Every tab renders with continuous login enabled").toPass({ timeout: 35_000 });

            return opened;
        });

        const waiting = await test.step("Only one tab leaves for the source", async () => {
            const isAway = (tab: Page) => !tab.url().startsWith(baseURL!);

            await expect
                .poll(() => tabs.filter(isAway).length, { message: "One tab leaves" })
                .toBe(1);

            const remaining = tabs.filter((tab) => !isAway(tab));

            for (const tab of remaining) {
                await expect(
                    tab.locator(IDENTIFICATION_STAGE),
                    "Waiting tab stays on the identification stage",
                ).toBeVisible();
            }

            return remaining;
        });

        await test.step("Authenticate in another tab", async () => {
            await page.goto(FLOW_WITH_NEXT);
            await session.login({ to: USER_INTERFACE_PATHNAME });
        });

        await test.step("Waiting tabs resume without signing in", async () => {
            for (const tab of waiting) {
                await tab.waitForURL(`**${USER_INTERFACE_PATHNAME}**`, { timeout: 20_000 });
            }
        });
    });
});
