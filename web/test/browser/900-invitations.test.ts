import { expect, test } from "#e2e";

import { IDGenerator } from "@goauthentik/core/id";
import { series } from "@goauthentik/core/promises";

test.describe("Invitation Wizard", () => {
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
    // CodeMirror editor wedged the wizard's Next button into a permanently-disabled
    // state, because the change handler read `ev.detail.value` (the detail is a
    // CodeMirror ViewUpdate, so `.value` was undefined) and the resulting
    // `YAML.parse(undefined)` threw, marking the step invalid.
    test("Create invitation with custom attributes via new enrollment flow", async ({
        page,
        form,
        pointer,
    }, testInfo) => {
        const name = invitationNames.get(testInfo.testId)!;
        const seed = name.replace("invite-", "");
        const { fill } = form;
        const { click } = pointer;

        const dialog = page.getByRole("dialog", { name: "New Invitation Wizard" });
        const $next = page.getByTestId("wizard-navigation-next");
        const $editor = dialog.locator("ak-codemirror");

        await test.step("Open the create-flow wizard", async () => {
            await expect(dialog, "Wizard is initially closed").toBeHidden();

            await click("New Invitation options");
            await click("New Enrollment Flow", "menuitem");

            await expect(dialog, "Wizard opens").toBeVisible();
        });

        await test.step("Configure the new enrollment flow", async () => {
            // Create mode defers validation to the Next handler, so the step is valid
            // (and Next enabled) as soon as it loads — never wedged on "Loading…".
            await expect($next, "Next is enabled on the create-flow step").toBeEnabled();

            await series(
                [fill, "Flow name", `Invite Flow ${seed}`, dialog],
                [fill, "Invitation stage name", `invite-stage-${seed}`, dialog],
                [click, "Next", "button", dialog],
            );
        });

        await test.step("Fill invitation details", async () => {
            await expect($next, "Next is disabled until a name is provided").toBeDisabled();
            await fill("Name", name, dialog);
            await expect($next, "Next is enabled once a name is provided").toBeEnabled();
        });

        await test.step("Editing custom attributes keeps the step valid", async () => {
            await $editor.click();
            await page.keyboard.press("ControlOrMeta+a");
            await page.keyboard.type("department: engineering");

            await expect(
                $next,
                "Next stays enabled after editing custom attributes (#22637)",
            ).toBeEnabled();

            // Clearing the field must not wedge the step either.
            await $editor.click();
            await page.keyboard.press("ControlOrMeta+a");
            await page.keyboard.press("Delete");

            await expect(
                $next,
                "Next stays enabled after clearing custom attributes (#22637)",
            ).toBeEnabled();
        });

        await test.step("Create the invitation", async () => {
            await click("Next", "button", dialog);

            await expect(
                page.getByText("Successfully created invitation."),
                "Success message confirms the invitation was created",
            ).toBeVisible({ timeout: 10_000 });
        });

        await test.step("Finish and close the wizard", async () => {
            await $next.click();
            await expect(dialog, "Wizard closes after finishing").toBeHidden();
        });
    });
});
