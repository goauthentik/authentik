import { expect, test } from "#e2e";

import { IDGenerator } from "@goauthentik/core/id";

test.describe("Invitation form", () => {
    const invitationNames = new Map<string, string>();

    //#region Lifecycle

    test.beforeEach("Seed names", async ({ session }, { testId }) => {
        const seed = IDGenerator.randomID(6).toLowerCase();
        invitationNames.set(testId, `invite-${seed}`);

        await test.step("Authenticate", () =>
            session.login({ to: "/if/admin/flow/stages/invitations" }));
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
        const { fill, selectSearchValue } = form;
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

            await selectSearchValue("Flow", /default-source-enrollment/, $dialog);
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
        // The blueprint import in the middle of this test eats most of the default
        // budget on its own; the remaining steps still need room after it.
        test.setTimeout(90_000);

        const name = invitationNames.get(testInfo.testId)!;
        const seed = name.replace("invite-", "");
        const { fill, selectSearchValue } = form;
        const { click } = pointer;

        const $dialog = page.getByRole("dialog", { name: "New Invitation" });
        const $flowDialog = page.getByRole("dialog", { name: "New Enrollment Flow" });
        const $successDialog = page.getByRole("dialog", { name: "Invitation Details" });

        await test.step("Open the invitation form", async () => {
            await click("New Invitation", "button");

            await expect($dialog, "Form opens").toBeVisible();
        });

        await test.step("Open the stacked enrollment flow form via the flow select", async () => {
            await selectSearchValue("Flow", /Create a new enrollment flow/, $dialog);

            await expect($flowDialog, "Enrollment flow form opens on top").toBeVisible();
        });

        await test.step("Create the enrollment flow and invitation stage", async () => {
            await fill("Flow Name", `Invite Flow ${seed}`, $flowDialog);
            // Seed the slug too. It defaults to a fixed `enrollment-with-invitation`, and
            // the blueprint import upserts by slug — so without this every run targets the
            // same flow record and the assertion below reads back a previous run's name.
            await fill("Flow Slug", `invite-flow-${seed}`, $flowDialog);
            await fill("Invitation Stage Name", `invite-stage-${seed}`, $flowDialog);

            await click("Create Enrollment Flow", "button", $flowDialog);

            // Creating the flow posts a blueprint import, which builds the flow, the
            // invitation stage, and the binding between them in one synchronous request.
            // That runs well past the 5s default — measured at ~4.4s for the request and
            // ~5.4s to the dialog closing on a debug build.
            await expect($flowDialog, "Flow form closes after creation").toBeHidden({
                timeout: 20_000,
            });
            await expect($dialog, "Invitation form is still open underneath").toBeVisible();
        });

        await test.step("The newly created flow is selected", async () => {
            // Scoped to the view rather than the placeholder: `ak-flow-search` composes
            // three elements deep and each level carries a real input with the same
            // placeholder — the host, `ak-search-select`'s hidden value input holding the
            // flow UUID, and the view's display input. Only the last shows the label.
            await expect(
                $dialog.locator("ak-search-select-view").getByRole("textbox"),
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
