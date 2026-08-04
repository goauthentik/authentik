import { expect, test } from "#e2e";
import type { FormFixture } from "#e2e/fixtures/FormFixture";
import { NavigatorFixture } from "#e2e/fixtures/NavigatorFixture";
import type { PageFixtureInit } from "#e2e/fixtures/PageFixture";
import type { PointerFixture } from "#e2e/fixtures/PointerFixture";
import { SessionFixture } from "#e2e/fixtures/SessionFixture";
import { randomName } from "#e2e/utils/generators";

import { IDGenerator } from "@goauthentik/core/id";
import { series } from "@goauthentik/core/promises";

import { snakeCase } from "change-case";

const ADMIN_USERNAME = "akadmin";
const DAY = 24 * 60 * 60 * 1_000;

type Page = PageFixtureInit["page"];
type Browser = NonNullable<ReturnType<ReturnType<Page["context"]>["browser"]>>;

interface BrowserContext {
    page: Page;
    form: FormFixture;
    pointer: PointerFixture;
}

interface UserIdentity {
    displayName: string;
    username: string;
}

interface ScheduleOptions {
    action?: "Deactivate" | "Delete";
    revokeSessions?: boolean;
    revokeTokens?: boolean;
}

function dateTimeLocal(value: Date): string {
    const localValue = new Date(value.getTime() - value.getTimezoneOffset() * 60_000);

    return localValue.toISOString().slice(0, 16);
}

function nextMinute(): Date {
    const value = new Date();
    value.setSeconds(0, 0);
    value.setMinutes(value.getMinutes() + 1);

    return value;
}

/**
 * The interaction context for a slot-based modal wrapper (`ak-forms-modal`,
 * `ak-forms-confirm`, `ak-forms-delete-bulk`).
 *
 * These wrappers slot their content into `ak-modal`, whose `<dialog>` lives in a shadow
 * root, so the `dialog` element is not a DOM ancestor of any slotted field:
 * `getByRole("dialog", ...).getByRole("radio", ...)` matches nothing at all. The wrapper
 * element contains both the slotted fields and the dialog's own action buttons, so it is
 * what field interactions have to be scoped to. The `dialog` locator stays useful for
 * open/close assertions.
 */
function modalContent(page: Page, wrapper: string, contains?: string) {
    const modal = page.locator(wrapper);

    return contains ? modal.filter({ has: page.locator(contains) }) : modal;
}

/**
 * The pending-offboarding trigger on the user details page.
 *
 * Its label sits inside a `pf-tooltip`, whose shadow root keeps the text out of the
 * button's computed accessible name, so `getByRole("button", { name: ... })` matches
 * nothing. Matching on text content works, scoped to the user info card so the
 * offboarding list's "Cancel Offboardings" bulk button can't collide.
 */
function cancelOffboardingButton(page: Page) {
    return page
        .locator("ak-user-info-card")
        .getByRole("button")
        .filter({ hasText: "Cancel Offboarding" });
}

function offboardingFormContent(page: Page) {
    return modalContent(page, "ak-forms-modal", "ak-user-offboarding-form");
}

async function openAdminNavLink(
    { page }: BrowserContext,
    group: string,
    linkName: string,
): Promise<void> {
    const link = page.getByRole("link", { name: linkName, exact: true });

    await test.step(`Open ${linkName} from the admin navigation`, async () => {
        if (!(await link.isVisible())) {
            await page.getByRole("button", { name: `Expand ${group}` }).click();
        }

        await expect(link, `${linkName} navigation link is visible`).toBeVisible();
        await link.click();
    });
}

async function openAdminPage(
    context: BrowserContext,
    group: string,
    linkName: string,
    mainName: string,
) {
    await openAdminNavLink(context, group, linkName);

    const main = context.page.getByRole("main", { name: mainName });
    await expect(main, `${mainName} page is visible`).toBeVisible();

    return main;
}

async function openUsers(context: BrowserContext) {
    return openAdminPage(context, "Directory", "Users", "Users");
}

async function setUserPassword(
    { page, form, pointer }: BrowserContext,
    password: string,
): Promise<void> {
    await test.step("Set a password for the offboarding user", async () => {
        await pointer.click("Set password", "button");

        const dialog = page
            .getByRole("dialog")
            .filter({ has: page.getByRole("button", { name: "Set Password", exact: true }) });
        await expect(dialog, "Set password dialog opens").toBeVisible();
        await form.fill("New Password", password, dialog);
        await dialog.getByRole("button", { name: "Set Password", exact: true }).click();
        await expect(dialog, "Set password dialog closes").toBeHidden({ timeout: 10_000 });
    });
}

async function verifyLogin(
    browser: Browser,
    testName: string,
    username: string,
    password: string,
    expected: "accepted" | "rejected",
): Promise<void> {
    const browserContext = await browser.newContext();
    const page = await browserContext.newPage();
    const navigator = new NavigatorFixture(page, testName);
    const session = new SessionFixture({ page, testName, navigator });

    try {
        await session.toLoginPage();
        await session.login({ username, password });

        if (expected === "accepted") {
            await expect(
                page.getByRole("heading", { level: 1 }),
                "Active user can log in before offboarding",
            ).toHaveText("Application Dashboard", { timeout: 10_000 });
            return;
        }

        await expect(
            session.$authFailureMessage,
            "Deactivated user's credentials are rejected",
        ).toBeVisible({ timeout: 10_000 });
    } finally {
        await browserContext.close();
    }
}

async function createInternalUser(
    { page, form, pointer }: BrowserContext,
    identity: UserIdentity,
): Promise<void> {
    const { displayName, username } = identity;
    const dialog = page.getByRole("dialog", { name: "New User Wizard" });

    await test.step(`Create user ${username}`, async () => {
        await pointer.click("New User", "button");
        await expect(dialog, "New user dialog opens").toBeVisible();

        await dialog.getByRole("radio", { name: "Internal" }).click({ force: true });

        await series(
            [form.fill, /^Username/, username, dialog],
            [form.fill, /^Display Name/, displayName, dialog],
            [form.fill, /^Email Address/, `${username}@example.com`, dialog],
            [form.fill, /^Path/, "users", dialog],
        );

        await dialog.getByRole("button", { name: "Create" }).click();
        await expect(dialog, "New user dialog closes").toBeHidden({ timeout: 10_000 });
    });
}

async function createServiceAccount(
    { page, form, pointer }: BrowserContext,
    username: string,
): Promise<void> {
    const dialog = page.getByRole("dialog", { name: "New User Wizard" });
    const nextButton = dialog.getByTestId("wizard-navigation-next");

    await test.step(`Create service account ${username}`, async () => {
        await pointer.click("New User", "button");
        await expect(dialog, "New user dialog opens").toBeVisible();

        await dialog.getByRole("radio", { name: "Service Account" }).click({ force: true });
        await form.fill(/^Username/, username, dialog);

        await nextButton.click();
        await expect(dialog, "Service account credentials are shown").toBeVisible();

        await nextButton.click();
        await expect(dialog, "Service account dialog closes").toBeHidden({ timeout: 10_000 });
    });
}

async function openUserDetails({ page, form }: BrowserContext, username: string): Promise<void> {
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

async function createAndOpenInternalUser(
    context: BrowserContext,
    identity: UserIdentity,
): Promise<void> {
    await createInternalUser(context, identity);
    await openUserDetails(context, identity.username);
}

async function scheduleOffboarding(
    { page, form, pointer }: BrowserContext,
    scheduledAt: Date,
    { action = "Deactivate", revokeSessions = true, revokeTokens = true }: ScheduleOptions = {},
): Promise<void> {
    const dialog = page.getByRole("dialog", { name: "Schedule Offboarding" });
    const fields = offboardingFormContent(page);

    await test.step(`Schedule ${action.toLowerCase()} offboarding`, async () => {
        await pointer.click("Schedule Offboarding", "button");
        await expect(dialog, "Schedule offboarding dialog opens").toBeVisible();

        await expect(
            fields.getByRole("radio", { name: "Deactivate" }),
            "Deactivate is selected by default",
        ).toBeChecked();
        await expect(
            fields.getByRole("checkbox", { name: "Revoke sessions" }),
            "Session revocation is enabled by default",
        ).toBeChecked();
        await expect(
            fields.getByRole("checkbox", { name: "Revoke tokens" }),
            "Token revocation is enabled by default",
        ).toBeChecked();

        await form.setRadio("Action", action, fields);
        await form.fill(fields.getByLabel("Scheduled for"), dateTimeLocal(scheduledAt));
        await form.setInputCheck("Revoke sessions", revokeSessions, fields);
        await form.setInputCheck("Revoke tokens", revokeTokens, fields);

        await fields.getByRole("button", { name: "Schedule", exact: true }).click();
        await expect(dialog, "Schedule offboarding dialog closes").toBeHidden({
            timeout: 10_000,
        });
        await expect(
            cancelOffboardingButton(page),
            "Pending offboarding can be canceled",
        ).toBeVisible({ timeout: 10_000 });
    });
}

async function openOffboardingList(context: BrowserContext) {
    return openAdminPage(context, "Events", "Offboardings", "User Offboardings");
}

async function setOnlyPending(list: ReturnType<Page["getByRole"]>, value: boolean): Promise<void> {
    const filter = list.getByRole("checkbox", { name: "Only show pending offboardings" });

    if ((await filter.isChecked()) !== value) {
        await filter.click();
    }

    if (value) {
        await expect(filter, "Only pending offboardings filter is enabled").toBeChecked();
    } else {
        await expect(filter, "Only pending offboardings filter is disabled").not.toBeChecked();
    }
}

async function searchRows(
    { form }: BrowserContext,
    list: ReturnType<Page["getByRole"]>,
    query: string,
) {
    const searchInput = await form.findTextualInput(/search/i, list);
    await form.fill(searchInput, query);
    await searchInput.press("Enter");

    return list.getByRole("row").filter({ hasText: query });
}

async function waitUntilDue(scheduledAt: Date): Promise<void> {
    await expect
        .poll(() => Date.now(), {
            message: "Scheduled offboarding time has passed",
            timeout: 70_000,
            intervals: [500, 1_000],
        })
        .toBeGreaterThan(scheduledAt.getTime());
}

async function runDueOffboardings(context: BrowserContext) {
    const { form, pointer } = context;

    await test.step("Run the due offboarding schedule", async () => {
        await openAdminNavLink(context, "Dashboards", "System Tasks");

        // Unlike the table pages, System Tasks renders an unnamed `<main>`, so it has to
        // be addressed by its element rather than by role name.
        const systemTasks = context.page.locator("ak-system-tasks");
        await expect(systemTasks, "System Tasks page is visible").toBeVisible();

        await pointer.click("Schedules", "tab");

        const schedules = systemTasks.getByRole("tabpanel", { name: "Schedules" });
        await expect(schedules, "Schedules tab is visible").toBeVisible();

        const scheduleRow = await form.search("Execute due user offboardings.", schedules);
        await expect(scheduleRow, "Due offboarding schedule is visible").toBeVisible();

        const runButton = scheduleRow.locator("ak-action-button").getByRole("button");
        await runButton.click();
        await expect(runButton, "Due offboarding schedule request completes").toHaveAttribute(
            "aria-busy",
            "false",
            { timeout: 10_000 },
        );
    });
}

async function waitForOffboardingEvent(
    context: BrowserContext,
    username: string,
    action: "deactivate" | "delete",
) {
    const { form } = context;
    const eventLog = await openAdminPage(context, "Events", "Logs", "Event Log");

    const searchInput = await form.findTextualInput(/search/i, eventLog);
    const query = `action = "user_offboarded" and context.message = "User ${username} was offboarded (${action})"`;
    const eventRow = eventLog.getByRole("row", { name: /User was offboarded/ });

    await expect(async () => {
        await form.fill(searchInput, query);
        await searchInput.press("Enter");
        await expect(eventRow, "Matching offboarding event is visible").toBeVisible({
            timeout: 2_000,
        });
    }, "Offboarding event is eventually written").toPass({
        timeout: 30_000,
        intervals: [500, 1_000, 2_000],
    });

    await expect(eventRow, "Offboarding event is attributed to the scheduling admin").toContainText(
        ADMIN_USERNAME,
    );

    return eventRow;
}

test.describe("User offboarding", () => {
    const identities = new Map<string, UserIdentity>();

    test.beforeEach(
        "Prepare user identity",
        async ({ page, form, pointer, session }, { testId }) => {
            const seed = IDGenerator.randomID(6);
            const displayName = `${randomName(seed)} Offboarding (${seed})`;

            identities.set(testId, {
                displayName,
                username: snakeCase(displayName),
            });

            await test.step("Authenticate", async () => {
                await session.toLoginPage();
                await session.login();
                await expect(
                    page.getByRole("heading", { level: 1 }),
                    "User interface opens after authentication",
                ).toHaveText("Application Dashboard", { timeout: 10_000 });
                await pointer.click("Admin interface", "link");
                await openUsers({ page, form, pointer });
            });
        },
    );

    test("Schedules, lists, cancels, and reschedules an offboarding", async ({
        page,
        form,
        pointer,
    }, testInfo) => {
        const context = { page, form, pointer };
        const identity = identities.get(testInfo.testId)!;
        const scheduledAt = new Date(Date.now() + DAY);

        await createAndOpenInternalUser(context, identity);
        await scheduleOffboarding(context, scheduledAt, {
            action: "Delete",
            revokeSessions: false,
            revokeTokens: false,
        });

        let list = await openOffboardingList(context);
        const pendingFilter = list.getByRole("checkbox", {
            name: "Only show pending offboardings",
        });
        await expect(pendingFilter, "Pending filter is enabled by default").toBeChecked();

        let row = await form.search(identity.username, list);
        await expect(row, "Scheduled offboarding is listed").toBeVisible();
        await expect(row, "Offboarding action is listed").toContainText("Delete");
        await expect(row, "Offboarding status is listed").toContainText("Pending");
        await expect(row, "Scheduling administrator is listed").toContainText(ADMIN_USERNAME);

        await test.step("Navigate to the user from the offboarding list", async () => {
            await row.getByRole("link", { name: identity.username }).click();
            await expect(
                page.getByRole("heading", { name: identity.username, exact: true }).first(),
                "Offboarding user link opens the user details page",
            ).toBeVisible();
        });

        await test.step("Cancel from the user details page", async () => {
            await cancelOffboardingButton(page).click();

            const summary = modalContent(page, "ak-forms-confirm");
            // The confirm dialog's header is slotted as well, so the dialog element has
            // no computed accessible name to match on.
            const dialog = summary.getByRole("dialog");

            await expect(dialog, "Cancel offboarding dialog opens").toBeVisible();
            await expect(summary, "Cancel dialog shows the selected action").toContainText(
                "Action: Delete",
            );
            await expect(
                summary,
                "Cancel dialog shows session revocation is disabled",
            ).toContainText("Revoke sessions: No");
            await expect(summary, "Cancel dialog shows token revocation is disabled").toContainText(
                "Revoke tokens: No",
            );

            await summary.getByRole("button", { name: "Cancel offboarding" }).click();
            await expect(dialog, "Cancel offboarding dialog closes").toBeHidden({
                timeout: 10_000,
            });
            await expect(
                page.getByRole("button", { name: "Schedule Offboarding" }),
                "Canceled user can be rescheduled",
            ).toBeVisible({ timeout: 10_000 });
        });

        list = await openOffboardingList(context);
        await setOnlyPending(list, false);
        row = await form.search(identity.username, list);
        await expect(row, "Canceled offboarding remains in history").toContainText("Canceled");

        await row.getByRole("link", { name: identity.username }).click();
        await expect(
            page.getByRole("heading", { name: identity.username, exact: true }).first(),
            "Canceled offboarding user opens",
        ).toBeVisible();

        await scheduleOffboarding(context, new Date(Date.now() + 2 * DAY));
    });

    test("Rejects an offboarding scheduled in the past", async ({
        page,
        form,
        pointer,
    }, testInfo) => {
        const context = { page, form, pointer };
        const identity = identities.get(testInfo.testId)!;

        await createAndOpenInternalUser(context, identity);

        const dialog = page.getByRole("dialog", { name: "Schedule Offboarding" });
        await pointer.click("Schedule Offboarding", "button");
        await expect(dialog, "Schedule offboarding dialog opens").toBeVisible();

        const fields = offboardingFormContent(page);
        const scheduledInput = fields.getByLabel("Scheduled for");
        await form.fill(scheduledInput, dateTimeLocal(new Date(Date.now() - DAY)));

        expect(
            await scheduledInput.evaluate(
                (element: HTMLInputElement) => element.validity.rangeUnderflow,
            ),
            "Past scheduled time violates the input minimum",
        ).toBe(true);

        await fields.getByRole("button", { name: "Schedule", exact: true }).click();
        await expect(dialog, "Invalid offboarding remains unscheduled").toBeVisible();
        await fields.getByRole("button", { name: "Cancel", exact: true }).click();
    });

    test("Hides self-offboarding while allowing regular service accounts", async ({
        page,
        form,
        pointer,
    }, testInfo) => {
        const context = { page, form, pointer };
        const identity = identities.get(testInfo.testId)!;

        await openUserDetails(context, ADMIN_USERNAME);
        await expect(
            page.getByRole("button", { name: "Schedule Offboarding" }),
            "Current administrator cannot schedule their own offboarding",
        ).toBeHidden();

        await openUsers(context);
        await createServiceAccount(context, identity.username);
        await openUserDetails(context, identity.username);

        await expect(
            page.getByRole("button", { name: "Schedule Offboarding" }),
            "Regular service accounts remain eligible for offboarding",
        ).toBeVisible();
    });

    test("Bulk-cancels pending offboardings", async ({ page, form, pointer }, testInfo) => {
        const context = { page, form, pointer };
        const identity = identities.get(testInfo.testId)!;
        const sharedUsername = `${identity.username}_bulk`;
        const users: UserIdentity[] = [
            {
                displayName: `${identity.displayName} Bulk One`,
                username: `${sharedUsername}_one`,
            },
            {
                displayName: `${identity.displayName} Bulk Two`,
                username: `${sharedUsername}_two`,
            },
        ];

        for (const [index, user] of users.entries()) {
            if (index > 0) {
                await openUsers(context);
            }
            await createAndOpenInternalUser(context, user);
            await scheduleOffboarding(context, new Date(Date.now() + (index + 1) * DAY));
        }

        const list = await openOffboardingList(context);
        const rows = await searchRows(context, list, sharedUsername);
        await expect(rows, "Both pending offboardings are listed").toHaveCount(2, {
            timeout: 10_000,
        });

        for (const row of await rows.all()) {
            await row.getByRole("checkbox").check();
        }

        await pointer.click("Cancel Offboardings", "button", list);

        const bulk = modalContent(page, "ak-forms-delete-bulk").first();
        const dialog = page.getByRole("dialog").filter({ hasText: "Cancel Offboardings" });

        await expect(dialog, "Bulk cancellation dialog opens").toBeVisible();
        await expect(bulk, "Bulk cancellation includes both users").toContainText(
            users[0].username,
        );
        await expect(bulk, "Bulk cancellation includes both users").toContainText(
            users[1].username,
        );

        await bulk.getByRole("button", { name: "Cancel Offboardings" }).last().click();
        await expect(dialog, "Bulk cancellation dialog closes").toBeHidden({ timeout: 10_000 });
        await expect(rows, "Canceled offboardings leave the pending list").toHaveCount(0, {
            timeout: 10_000,
        });

        await setOnlyPending(list, false);
        const canceledRows = await searchRows(context, list, sharedUsername);
        await expect(canceledRows, "Canceled offboardings remain in history").toHaveCount(2, {
            timeout: 10_000,
        });
        for (const row of await canceledRows.all()) {
            await expect(row, "Bulk-canceled offboarding has canceled status").toContainText(
                "Canceled",
            );
        }
    });

    test("Executes a scheduled user deactivation", async ({
        page,
        form,
        pointer,
        browser,
    }, testInfo) => {
        // Waits for a schedule to fall due (up to a minute), runs it, then polls the
        // event log — well past the default per-test timeout.
        test.setTimeout(240_000);

        const context = { page, form, pointer };
        const identity = identities.get(testInfo.testId)!;
        const password = `Ak-${IDGenerator.randomID(20)}!`;

        await createAndOpenInternalUser(context, identity);
        await setUserPassword(context, password);
        await verifyLogin(browser, testInfo.title, identity.username, password, "accepted");

        // Pinned here rather than at the top of the test: the setup above can outlast the
        // next minute boundary, and a scheduled time in the past fails the input minimum.
        const scheduledAt = nextMinute();

        await scheduleOffboarding(context, scheduledAt);
        await waitUntilDue(scheduledAt);
        await runDueOffboardings(context);

        const eventRow = await waitForOffboardingEvent(context, identity.username, "deactivate");
        await eventRow.getByRole("link").last().click();
        await expect(page.locator("pre"), "Audit event retains the target username").toContainText(
            identity.username,
        );

        await openUsers(context);
        await openUserDetails(context, identity.username);

        // The `term` role does not take its name from content, so the Active row is
        // reached from its `dt` across to the paired `dd` instead.
        const activeStatus = page
            .locator("ak-user-info-card")
            .locator("dt", { hasText: /^Active$/ })
            .locator("xpath=following-sibling::dd")
            .getByRole("status");

        await expect(
            activeStatus,
            "Executed deactivation marks the user inactive",
        ).toHaveAccessibleName("No");
        await expect(
            page.getByRole("button", { name: "Schedule Offboarding" }),
            "Completed offboarding is no longer pending",
        ).toBeVisible();

        const list = await openOffboardingList(context);

        // The table can still be holding its pre-execution render, and re-submitting an
        // unchanged search query does not refetch it, so reload between attempts.
        await expect(async () => {
            await page.reload();
            await expect(list, "Offboarding list is visible").toBeVisible({ timeout: 10_000 });

            await setOnlyPending(list, false);

            const completedRow = await form.search(identity.username, list);

            await expect(completedRow, "Row reports the completed status").toContainText(
                "Completed",
                { timeout: 2_000 },
            );
        }, "Completed deactivation appears in history").toPass({
            timeout: 90_000,
            intervals: [2_000, 3_000],
        });

        await verifyLogin(browser, testInfo.title, identity.username, password, "rejected");
    });

    test("Executes a scheduled user deletion and retains its audit event", async ({
        page,
        form,
        pointer,
    }, testInfo) => {
        test.setTimeout(240_000);

        const context = { page, form, pointer };
        const identity = identities.get(testInfo.testId)!;

        await createAndOpenInternalUser(context, identity);

        const scheduledAt = nextMinute();

        await scheduleOffboarding(context, scheduledAt, { action: "Delete" });
        await waitUntilDue(scheduledAt);
        await runDueOffboardings(context);

        const eventRow = await waitForOffboardingEvent(context, identity.username, "delete");
        await eventRow.getByRole("link").last().click();

        const rawEvent = page.locator("pre");
        await expect(rawEvent, "Delete audit event remains available").toContainText(
            identity.username,
        );
        await expect(rawEvent, "Delete audit event records the selected action").toContainText(
            '"offboarding_action": "delete"',
        );

        const usersList = await openUsers(context);
        const deletedRows = await searchRows(context, usersList, identity.username);
        await expect(deletedRows, "Deleted user is removed from the users list").toHaveCount(0, {
            timeout: 10_000,
        });
    });
});
