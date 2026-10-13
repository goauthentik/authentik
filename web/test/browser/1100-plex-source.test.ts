import { expect, test } from "#e2e";
import { plexCredentials } from "#e2e/fixtures/PlexFixture";

import { IDGenerator } from "@goauthentik/core/id";

import type { Page } from "@playwright/test";

test.describe("Plex source", { tag: "@plex" }, () => {
    // Also gated in the Playwright config; this covers runs that bypass it.
    test.skip(
        !plexCredentials(),
        "Signs in to plex.tv. Set AK_TEST_PLEX_EMAIL and AK_TEST_PLEX_PASSWORD to run it.",
    );

    test("Sign in through a new Plex source", async ({
        session,
        flows,
        plex,
        browser,
        baseURL,
    }) => {
        const seed = IDGenerator.randomID(6).toLowerCase();
        const sourceName = `Plex ${seed}`;
        const flowSlug = `plex-login-${seed}`;

        await test.step("Authenticate", () => session.login({ to: "/if/admin/core/sources" }));

        await test.step("Create the source", () =>
            plex.createSource({ name: sourceName, slug: `plex-${seed}` }));

        await test.step("Create a login flow offering the source", async () => {
            await flows.createFlow(`Plex login ${seed}`, flowSlug);

            await flows.bindIdentificationStage({
                flowSlug,
                name: `plex-identification-${seed}`,
                sources: [sourceName],
            });
        });

        // The admin's browser is signed in to both authentik and plex.tv by now; the sign-in
        // under test starts from neither.
        const visitorContext = await browser.newContext({ baseURL });
        const visitor = await visitorContext.newPage();
        const popups: Page[] = [];

        visitor.on("popup", (popup) => popups.push(popup));

        await test.step("Leave for Plex in the same tab", async () => {
            await visitor.goto(`/if/flow/${flowSlug}/?next=%2Fif%2Fuser%2F`);

            await visitor.getByRole("button", { name: `Continue with ${sourceName}` }).click();

            await visitor.waitForURL(/^https:\/\/app\.plex\.tv\/auth/, { timeout: 30_000 });

            const forwardUrl = new URLSearchParams(new URL(visitor.url()).hash.slice(2)).get(
                "forwardUrl",
            );

            expect(forwardUrl, "Plex is told to return to the flow, keeping next").toBe(
                new URL(`/if/flow/${flowSlug}/?next=%2Fif%2Fuser%2F`, baseURL).href,
            );

            expect(popups, "No popup is opened").toHaveLength(0);
        });

        await test.step("Sign in at Plex", () => plex.signIn(visitor));

        await test.step("Return signed in as the Plex user", async () => {
            await visitor.waitForURL(
                (url) => url.origin === new URL(baseURL!).origin && url.pathname === "/if/user/",
                { timeout: 60_000 },
            );

            // Users enrolled through a source are external, and external users are turned
            // away from the user interface. Only a signed-in user gets this far, so the
            // message is what confirms the sign-in completed.
            await expect(
                visitor.getByText("Interface can only be accessed by internal users"),
                "Flow completes and signs in the Plex user",
            ).toBeVisible();
        });

        await visitorContext.close();
    });
});
