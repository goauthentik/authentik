import { expect, test } from "#e2e";
import { FormFixture } from "#e2e/fixtures/FormFixture";
import { LicenseFixture } from "#e2e/fixtures/LicenseFixture";
import { NavigatorFixture } from "#e2e/fixtures/NavigatorFixture";
import { SessionFixture } from "#e2e/fixtures/SessionFixture";
import { randomName } from "#e2e/utils/generators";

import { IDGenerator } from "@goauthentik/core/id";
import { series } from "@goauthentik/core/promises";

import type { Browser, Page } from "@playwright/test";
import { snakeCase } from "change-case";

const DEFAULT_BRAND_DOMAIN = "authentik-default";

/**
 * The lockdown flow this suite builds for itself.
 *
 * Nothing ships a lockdown flow by default and the feature stays inert until a brand
 * points at one, so the suite creates the flow, its stage, and the binding through the
 * admin UI before any test runs, then drives the one field an operator configures.
 */
const LOCKDOWN_FLOW_SLUG = "test-account-lockdown";
const LOCKDOWN_FLOW_NAME = "Test - Account lockdown";
const LOCKDOWN_STAGE_NAME = "test-account-lockdown-stage";
const LOCKDOWN_FLOW = new RegExp(LOCKDOWN_FLOW_SLUG);

/**
 * Where the lockdown stage sends a user whose own session it just deleted. Any
 * unauthenticated flow works; the default authentication flow always exists.
 *
 * A string, not a pattern: `selectSearchValue` only types into the control when given
 * one, and without typing it matches against whichever options the picker happened to
 * load first. The stage saves silently without this and only fails much later, when a
 * self-lockdown is denied for having no completion flow.
 */
const COMPLETION_FLOW = "default-authentication-flow";

/**
 * The password given to the account each test locks down, so that the lockdown's effect
 * on authentication is observable rather than inferred.
 */
const TARGET_PASSWORD = "e2e-account-lockdown-target";

interface TargetUser {
    displayName: string;
    username: string;
    email: string;
}

/**
 * The `Active` row of the user info card.
 *
 * The ARIA `term` role does not take its name from content, so the row is reached from
 * its `dt` across to the paired `dd`.
 */
function activeStatus(page: Page) {
    return page
        .locator("ak-user-info-card")
        .locator("dt", { hasText: /^Active$/ })
        .locator("xpath=following-sibling::dd")
        .getByRole("status");
}

/**
 * Create the lockdown flow, its stage, and the binding between them, unless a previous
 * run already left them behind.
 *
 * Driven through the admin UI rather than seeded, so the suite carries its own
 * prerequisite and does not depend on a blueprint the test runner never applies.
 */
async function ensureLockdownFlow(
    page: Page,
    form: FormFixture,
    navigator: NavigatorFixture,
): Promise<void> {
    await navigator.navigate("/if/admin/flow/flows");

    // `form.search` retries for ~15s before throwing. On a fresh instance that cost is
    // paid once, for the whole suite, and it keeps the probe on the sanctioned fixture
    // rather than a hand-rolled table query.
    const alreadySeeded = await test.step("Look for an existing lockdown flow", () =>
        form
            .search(LOCKDOWN_FLOW_SLUG)
            .then(() => true)
            .catch(() => false));

    if (!alreadySeeded) {
        await test.step("Create the lockdown flow", async () => {
            const dialog = page.getByRole("dialog", { name: "New Flow" });

            // The probe leaves the table filtered to nothing, and its empty state offers
            // a second "New Flow" button beside the toolbar's.
            await page.getByRole("button", { name: "New Flow" }).first().click();
            await expect(dialog, "New Flow dialog opens").toBeVisible();

            await series(
                [form.fill, "Flow Name", LOCKDOWN_FLOW_NAME, dialog],
                [form.fill, "Title", "Account lockdown", dialog],
                [form.fill, "Slug", LOCKDOWN_FLOW_SLUG, dialog],
            );

            await dialog.locator("select#designation").selectOption("stage_configuration");
            // The stage deletes the target's sessions, so the flow must not require an
            // authenticated session of its own.
            await dialog.locator("select#authentication").selectOption("none");

            await dialog.getByRole("button", { name: "Create Flow" }).click();
            await expect(dialog, "New Flow dialog closes").toBeHidden({ timeout: 15_000 });
        });
    }

    await test.step("Open the lockdown flow", async () => {
        const row = await form.search(LOCKDOWN_FLOW_SLUG);

        await row.getByRole("link").first().click();

        await expect(page.locator("ak-flow-view"), "Flow detail page opens").toBeVisible({
            timeout: 15_000,
        });

        await page.getByRole("tab", { name: "Stage Bindings" }).click();
    });

    const binding = page.getByRole("row", { name: new RegExp(LOCKDOWN_STAGE_NAME) });

    // Checked separately from the flow: a run interrupted between creating the flow and
    // binding its stage leaves a flow that exists but does nothing, and the suite would
    // then skip setup and fail much later on an inert lockdown.
    const alreadyBound = await binding
        .first()
        .waitFor({ state: "visible", timeout: 5_000 })
        .then(() => true)
        .catch(() => false);

    if (alreadyBound) return;

    await test.step("Create and bind the lockdown stage", async () => {
        const dialog = page.getByRole("dialog", { name: "New Stage Wizard" });

        await page
            .getByRole("button", { name: /Create or bind/i })
            .first()
            .click();

        await expect(dialog, "Stage wizard opens").toBeVisible();

        // Slotted content keeps Playwright from considering the radio visible, the same
        // reason `300-users.test.ts` forces its "Internal" click. Choosing a type
        // advances the wizard on its own.
        await dialog
            .getByRole("radio", { name: "Account Lockdown Stage", exact: true })
            .click({ force: true });

        // Suffixed, so a partially-completed earlier run cannot collide on the stage
        // name and bounce the wizard back with a uniqueness error.
        const stageName = `${LOCKDOWN_STAGE_NAME}-${IDGenerator.randomID(6)}`;

        await test.step("Describe the stage", async () => {
            await form.fill("Stage Name", stageName, dialog);
            await form.selectSearchValue("Completion flow", COMPLETION_FLOW, dialog);

            await dialog.getByRole("button", { name: "Next" }).click();
        });

        await test.step("Bind it to the flow", async () => {
            // The wizard creates the stage on leaving the previous step but does not
            // carry it into the binding, and the picker's options were fetched before it
            // existed — so pass the name as a string, which types into the search select
            // and refetches, rather than a pattern that only filters what is loaded.
            // Addressed by placeholder: the visible "Stage" label is loose text with no
            // association to the control, so a "Stage" name match lands on the previous
            // step's "Stage Name" box, which the wizard keeps mounted.
            await form.selectSearchValue(/Select a stage/i, stageName, dialog);

            // Order and policy mode keep their defaults. "Create" rather than "Next":
            // this is the wizard's last step.
            await dialog.getByRole("button", { name: "Create", exact: true }).click();
        });

        await expect(dialog, "Stage wizard closes").toBeHidden({ timeout: 15_000 });

        await expect(
            page.getByRole("row", { name: new RegExp(stageName) }),
            "Stage is bound to the lockdown flow",
        ).toBeVisible({ timeout: 15_000 });
    });
}

test.describe("Account lockdown", () => {
    // Serial, because every test here depends on one piece of global state: the default
    // brand's account lockdown flow. `playwright.config.js` sets `fullyParallel`, so
    // without this the per-worker `beforeAll` hooks race writing the same brand row.
    test.describe.configure({ mode: "serial" });

    const targets = new Map<string, TargetUser>();

    //#region Lifecycle

    test.beforeAll(
        "Ensure the default brand has an account lockdown flow",
        async ({ browser }, { title: testName }) => {
            const context = await browser.newContext();
            const page = await context.newPage();
            const navigator = new NavigatorFixture(page, testName);
            const form = new FormFixture(page, testName);
            const session = new SessionFixture({ page, testName, navigator });

            await test.step("Authenticate", async () =>
                session.login({ to: "/if/admin/core/brands", page }));

            const licensed = await new LicenseFixture({ page, testName }).isAvailable();

            if (!licensed) {
                await context.close();
            }

            test.skip(!licensed, "A valid enterprise license is required");

            await ensureLockdownFlow(page, form, navigator);

            await navigator.navigate("/if/admin/core/brands");

            const $brand = await test.step("Find the default brand via search", () =>
                form.search(DEFAULT_BRAND_DOMAIN, page));

            await $brand.getByRole("button", { name: /^Edit .*Brand$/ }).click();

            const dialog = page.getByRole("dialog", { name: "Edit Brand" });
            await expect(dialog, "Edit modal opens after clicking edit").toBeVisible();

            await form.setFormGroup("Default flows", true, dialog);

            const $flowSearch = dialog.getByRole("textbox", { name: "Account lockdown flow" });
            const configuredFlow = await $flowSearch.inputValue();

            if (LOCKDOWN_FLOW.test(configuredFlow)) {
                // Already configured by an earlier run. Leaving the row alone keeps this
                // hook read-only so repeat runs cannot race on the brand.
                await dialog.getByRole("button", { name: "Cancel" }).click();
            } else {
                await form.selectSearchValue("Account lockdown flow", LOCKDOWN_FLOW, dialog);

                await dialog.getByRole("button", { name: "Save Changes" }).click();
            }

            await expect(dialog, "Edit modal closes").toBeHidden({ timeout: 15_000 });

            await context.close();
        },
    );

    test.beforeEach("Seed target account details", async ({ page: _page }, { testId }) => {
        const seed = IDGenerator.randomID(6);
        const displayName = `${randomName(seed)} Lockdown (${seed})`;
        const username = snakeCase(displayName);

        targets.set(testId, { displayName, username, email: `${username}@example.com` });
    });

    //#endregion

    //#region Helpers

    /**
     * Create an internal account with a known password, through the admin UI.
     */
    async function createTargetUser(
        { form, page }: { form: FormFixture; page: Page },
        user: TargetUser,
    ): Promise<void> {
        const { fill, search } = form;

        await test.step("Create the target account", async () => {
            const dialog = page.getByRole("dialog", { name: "New User Wizard" });

            await page.getByRole("button", { name: "New User" }).click();
            await expect(dialog, "Create dialog opens").toBeVisible();

            // `force` matches `300-users.test.ts`: buttons with slotted content are not
            // considered visible by Playwright.
            await dialog.getByRole("radio", { name: "Internal" }).click({ force: true });

            await series(
                [fill, /^Username/, user.username, dialog],
                [fill, /^Display Name/, user.displayName, dialog],
                [fill, /^Email Address/, user.email, dialog],
                [fill, /^Path/, "users", dialog],
            );

            await dialog.getByRole("button", { name: "Create" }).click();
            await expect(dialog, "Create dialog closes").toBeHidden({ timeout: 10_000 });
        });

        await test.step("Set the target account's password", async () => {
            const $user = await search(user.username);
            await expect($user, "Target account is visible").toBeVisible();

            await $user.getByRole("button", { name: "Expand row" }).click();

            const setPassword = page.getByRole("button", { name: "Set password" });
            await expect(setPassword, "Set password button is revealed").toBeVisible();
            await setPassword.click();

            const dialog = page.getByRole("dialog", { name: /password$/i });
            await expect(dialog, "Set password dialog opens").toBeVisible();

            await dialog.getByLabel("New Password").fill(TARGET_PASSWORD);
            await dialog.getByRole("button", { name: "Set Password" }).click();
            await expect(dialog, "Set password dialog closes").toBeHidden({ timeout: 10_000 });
        });
    }

    async function openUserDetails(
        { form, page }: { form: FormFixture; page: Page },
        username: string,
    ): Promise<void> {
        await test.step(`Open user ${username}`, async () => {
            const row = await form.search(username);
            await expect(row, "User is visible in the users table").toBeVisible();

            const viewLink = row.getByRole("link", { name: /view details/i });
            await expect(viewLink, "User details link is visible").toBeVisible();
            await viewLink.click();

            await expect(
                page.getByRole("heading", { name: username, exact: true }).first(),
                "User details page opens",
            ).toBeVisible();
        });
    }

    /**
     * Attempt a login in a throwaway browser context, so the admin session is untouched.
     */
    async function attemptLogin(
        browser: Browser,
        testName: string,
        username: string,
        expected: "accepted" | "rejected",
    ): Promise<void> {
        const context = await browser.newContext();
        const page = await context.newPage();
        const navigator = new NavigatorFixture(page, testName);
        const session = new SessionFixture({ page, testName, navigator });

        try {
            await session.toLoginPage();
            await session.login({ username, password: TARGET_PASSWORD });

            if (expected === "accepted") {
                await expect(
                    page.getByRole("heading", { level: 1 }),
                    "Target account can sign in before lockdown",
                ).toHaveText("Application Dashboard", { timeout: 10_000 });

                return;
            }

            await expect(
                session.$authFailureMessage,
                "Locked-down account's credentials are rejected",
            ).toBeVisible({ timeout: 10_000 });
        } finally {
            await context.close();
        }
    }

    /**
     * Sign in as the target account and lock it from the user settings, in a throwaway
     * context so the admin session is untouched.
     */
    async function lockOwnAccount(
        browser: Browser,
        testName: string,
        username: string,
    ): Promise<void> {
        const context = await browser.newContext();
        const page = await context.newPage();
        const navigator = new NavigatorFixture(page, testName);
        const session = new SessionFixture({ page, testName, navigator });

        try {
            await test.step("Sign in as the target account", async () => {
                await session.toLoginPage();
                // The authentication flow lands on the library, so settings is a separate
                // navigation rather than the login's wait target.
                await session.login({ username, password: TARGET_PASSWORD, to: "if/user/" });
                await navigator.navigate("/if/user/settings");
            });

            await test.step("Lock the account from user settings", async () => {
                await page.getByRole("tab", { name: "Security" }).click();

                const lockButton = page.getByRole("button", { name: "Lock my account" });

                await expect(
                    lockButton,
                    "Self-service lockdown is offered under Security",
                ).toBeVisible({ timeout: 10_000 });

                await lockButton.click();

                // The stage deletes this session, so the flow hands the user off to the
                // stage's configured completion flow.
                await expect(
                    session.$identificationStage,
                    "Self-service lockdown ends the session at the completion flow",
                ).toBeVisible({ timeout: 20_000 });
            });
        } finally {
            await context.close();
        }
    }

    //#endregion

    //#region Tests

    test("Locks down a target account", async ({
        session,
        navigator,
        form,
        page,
        browser,
    }, testInfo) => {
        test.setTimeout(180_000);

        const user = targets.get(testInfo.testId)!;
        const context = { form, page };

        await test.step("Authenticate as the administrator", async () => {
            await session.login({ to: "/if/admin/identity/users" });
        });

        await createTargetUser(context, user);

        await attemptLogin(browser, testInfo.title, user.username, "accepted");

        await openUserDetails(context, user.username);

        await expect(activeStatus(page), "Target account starts out active").toHaveAccessibleName(
            "Yes",
        );

        await test.step("Run the account lockdown flow", async () => {
            const lockdown = page.getByRole("button", { name: "Account Lockdown" });

            await expect(lockdown, "Account Lockdown action is offered").toBeVisible();
            await lockdown.click();

            // The action only *starts* the flow; the browser follows the returned link and
            // the stage executes inside the flow executor.
            await page.waitForURL(/\/if\/flow\//, { timeout: 20_000 });
        });

        await test.step("Verify the account is locked down", async () => {
            // The admin session survives locking down someone else, so navigate rather
            // than re-authenticate.
            await navigator.navigate("/if/admin/identity/users");
            await openUserDetails(context, user.username);

            await expect(
                activeStatus(page),
                "Lockdown deactivates the target account",
            ).toHaveAccessibleName("No", { timeout: 15_000 });
        });

        await attemptLogin(browser, testInfo.title, user.username, "rejected");
    });

    test("Locks down the signed-in user's own account", async ({
        session,
        navigator,
        form,
        page,
        browser,
    }, testInfo) => {
        test.setTimeout(180_000);

        const user = targets.get(testInfo.testId)!;
        const context = { form, page };

        await test.step("Authenticate as the administrator", async () => {
            await session.login({ to: "/if/admin/identity/users" });
        });

        await createTargetUser(context, user);

        await attemptLogin(browser, testInfo.title, user.username, "accepted");

        await lockOwnAccount(browser, testInfo.title, user.username);

        await test.step("Verify the account is locked down", async () => {
            await navigator.navigate("/if/admin/identity/users");
            await openUserDetails(context, user.username);

            await expect(
                activeStatus(page),
                "Self-service lockdown deactivates the account",
            ).toHaveAccessibleName("No", { timeout: 15_000 });
        });

        await attemptLogin(browser, testInfo.title, user.username, "rejected");
    });

    test("Hides the lockdown action for the administrator's own account", async ({
        session,
        form,
        page,
    }) => {
        await test.step("Authenticate as the administrator", async () => {
            await session.login({ to: "/if/admin/identity/users" });
        });

        await openUserDetails({ form, page }, "akadmin");

        await expect(
            page.getByRole("button", { name: "Account Lockdown" }),
            "Administrators cannot lock down their own account from the user details page",
        ).toBeHidden();
    });

    //#endregion
});
