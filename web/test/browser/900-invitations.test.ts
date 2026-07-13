import { expect, test } from "#e2e";

import { IDGenerator } from "@goauthentik/core/id";

test.describe("Invitation form", () => {
    const invitationNames = new Map<string, string>();

    //#region Lifecycle

    test.beforeEach("Seed names", async ({ session }, { testId }) => {
        const seed = IDGenerator.randomID(6).toLowerCase();
        invitationNames.set(testId, `invite-${seed}`);

        await test.step("Authenticate", () =>
            session.login({ to: "/if/admin/#/flow/stages/invitations" }));
    });

    test.afterEach("Verify invitation was created", async ({ form }, { testId }) => {
        const name = invitationNames.get(testId)!;
        const $invitation = await test.step("Find invitation via search", () => form.search(name));

        await expect($invitation, "Invitation is visible in the table").toBeVisible();
    });

    //#endregion

    // Regression for goauthentik/authentik#22637: typing custom attributes into the
    // CodeMirror editor must not block submission.
    test("Create invitation with custom attributes", async ({ page, form, pointer }, testInfo) => {
        const name = invitationNames.get(testInfo.testId)!;
        const { fill } = form;
        const { click } = pointer;

        const $dialog = page.getByRole("dialog", { name: "New Invitation" });
        const $successDialog = page.getByRole("dialog", { name: "Invitation Details" });
        const $editor = $dialog.locator("ak-codemirror");

        await test.step("Open the invitation form", async () => {
            await expect($dialog, "Form is initially closed").toBeHidden();

            await click("New Invitation", "button");

            await expect($dialog, "Form opens").toBeVisible();
        });

        await test.step("Fill invitation details", async () => {
            await fill("Invitation Name", name, $dialog);

            await $dialog.getByPlaceholder("Select a flow...").click();
            await page.getByRole("option", { name: /default-source-enrollment/ }).click();
        });

        await test.step("Edit custom attributes (#22637)", async () => {
            await $editor.click();
            await page.keyboard.press("ControlOrMeta+a");
            await page.keyboard.type("department: engineering");
        });

        await test.step("Create the invitation", async () => {
            await click("Create Invitation", "button", $dialog);

            await expect(
                page.getByText("Successfully created invitation."),
                "Success message confirms the invitation was created",
            ).toBeVisible({ timeout: 10_000 });
        });

        await test.step("Success modal presents the invitation link", async () => {
            await expect($successDialog, "Success modal opens").toBeVisible();

            await expect(
                $successDialog.getByRole("button", { name: "Copy Link" }),
                "Copy Link action is available",
            ).toBeVisible();

            await expect(
                $successDialog.getByRole("button", { name: "Send via Email" }),
                "Send via Email action is available",
            ).toBeVisible();

            await $successDialog.getByRole("button", { name: "Close", exact: true }).click();

            await expect($successDialog, "Success modal closes").toBeHidden();
        });
    });

    test("Create enrollment flow with invitation stage from the flow select", async ({
        page,
        form,
        pointer,
    }, testInfo) => {
        const name = invitationNames.get(testInfo.testId)!;
        const seed = name.replace("invite-", "");
        const { fill } = form;
        const { click } = pointer;

        const $dialog = page.getByRole("dialog", { name: "New Invitation" });
        const $flowDialog = page.getByRole("dialog", { name: "New Enrollment Flow" });
        const $successDialog = page.getByRole("dialog", { name: "Invitation Details" });

        await test.step("Open the invitation form", async () => {
            await click("New Invitation", "button");

            await expect($dialog, "Form opens").toBeVisible();
        });

        await test.step("Open the stacked enrollment flow form via the flow select", async () => {
            await $dialog.getByPlaceholder("Select a flow...").click();

            await page.getByRole("option", { name: "Create a new enrollment flow" }).click();

            await expect($flowDialog, "Enrollment flow form opens on top").toBeVisible();
        });

        await test.step("Create the enrollment flow and invitation stage", async () => {
            await fill("Flow Name", `Invite Flow ${seed}`, $flowDialog);
            await fill("Invitation Stage Name", `invite-stage-${seed}`, $flowDialog);

            await click("Create Enrollment Flow", "button", $flowDialog);

            await expect($flowDialog, "Flow form closes after creation").toBeHidden();
            await expect($dialog, "Invitation form is still open underneath").toBeVisible();
        });

        await test.step("The newly created flow is selected", async () => {
            await expect(
                $dialog.getByPlaceholder("Select a flow..."),
                "Flow search adopts the newly created flow",
            ).toHaveValue(new RegExp(seed));
        });

        await test.step("Create the invitation", async () => {
            await fill("Invitation Name", name, $dialog);

            await click("Create Invitation", "button", $dialog);

            await expect($successDialog, "Success modal opens").toBeVisible({ timeout: 10_000 });

            await $successDialog.getByRole("button", { name: "Close", exact: true }).click();
        });
    });
});
