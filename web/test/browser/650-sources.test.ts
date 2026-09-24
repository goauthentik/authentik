import { expect, test } from "#e2e";
import { randomName } from "#e2e/utils/generators";

import { IDGenerator } from "@goauthentik/core/id";
import { series } from "@goauthentik/core/promises";

test.describe("Sources", () => {
    const names = new Map<string, string>();

    test.beforeEach("Seed names", async ({ page: _page }, { testId }) => {
        const seed = IDGenerator.randomID(6);
        names.set(testId, `${randomName(seed)} (${seed})`);
    });

    test("Persist LDAP source settings through creation and editing", async ({
        session,
        navigator,
        form,
        pointer,
        page,
    }, testInfo) => {
        const name = names.get(testInfo.testId)!;
        const groups = [`${name} first parent`, `${name} second parent`];

        const { fill, search, selectSearchValue, setInputCheck, setFormGroup, legacyTextInput } =
            form;

        const { click } = pointer;

        await test.step("Create parent groups", async () => {
            await session.login({ to: "/if/admin/identity/groups" });
            const dialog = page.getByRole("dialog", { name: "New Group" });

            for (const group of groups) {
                await click("New Group", "button");
                await expect(dialog, "Group dialog opens").toBeVisible();
                await fill(/^Group Name/, group, dialog);
                await click("Create Group", "button", dialog);
                await expect(dialog, "Group dialog closes after creation").toBeHidden();
            }
        });

        await test.step("Create an LDAP source with non-default settings", async () => {
            await navigator.navigate("/if/admin/core/sources");

            await page
                .locator('[part="toolbar-secondary"]')
                .getByRole("button", { name: "New Source" })
                .click();

            const dialog = page.getByRole("dialog", { name: "New Source Wizard" });
            await expect(dialog, "Source wizard opens").toBeVisible();
            await click("LDAP Source", "option", dialog);

            await series(
                [fill, legacyTextInput("Name", dialog), name],
                // This test exercises configuration persistence without an LDAP server.
                [setInputCheck, "Enabled", false, dialog],
                [setInputCheck, "Sync users", false, dialog],
                [setInputCheck, "Sync groups", false, dialog],
                [setInputCheck, "User password writeback", false, dialog],
                [fill, legacyTextInput("Server URI", dialog), "ldap://ldap.example.com"],
                [fill, legacyTextInput("Base DN", dialog), "dc=example,dc=com"],
                [setFormGroup, "Additional settings", true, dialog],
                [selectSearchValue, legacyTextInput("Additional Parent Group", dialog), groups[0]],
                [fill, legacyTextInput("User path", dialog), "sources/ldap-created"],
                [fill, legacyTextInput("Additional User DN", dialog), "ou=people"],
                [click, "Create", "button", dialog],
            );

            await expect(dialog, "Source wizard closes after creation").toBeHidden();
        });

        const dialog = page.getByRole("dialog", { name: "Edit LDAP Source" });

        const openEditor = async () => {
            // Navigate again so assertions use freshly retrieved data, not form state.
            await navigator.navigate("/if/admin/core/sources");
            const row = await search(name);
            await row.getByRole("button", { name: /^Edit/ }).click();
            await expect(dialog, "LDAP source editor opens").toBeVisible();
            await setFormGroup("Additional settings", true, dialog);
        };

        await test.step("Verify created settings and change the parent group", async () => {
            await openEditor();

            for (const label of [
                "Enabled",
                "Sync users",
                "Sync groups",
                "User password writeback",
            ]) {
                await expect(
                    dialog.getByRole("checkbox", { name: label, exact: true }),
                    `${label} remains disabled after creation`,
                ).not.toBeChecked();
            }

            await expect(
                legacyTextInput("Additional Parent Group", dialog),
                "Parent group persists on creation",
            ).toHaveValue(groups[0]);

            await expect(
                legacyTextInput("User path", dialog),
                "User path persists on creation",
            ).toHaveValue("sources/ldap-created");

            await expect(
                legacyTextInput("Additional User DN", dialog),
                "Additional user DN persists on creation",
            ).toHaveValue("ou=people");

            await series(
                [selectSearchValue, legacyTextInput("Additional Parent Group", dialog), groups[1]],
                [fill, legacyTextInput("User path", dialog), "sources/ldap-updated"],
                [fill, legacyTextInput("Additional User DN", dialog), "ou=users"],
                [click, "Save Changes", "button", dialog],
            );

            await expect(dialog, "Editor closes after updating settings").toBeHidden();
        });

        await test.step("Verify updated settings and clear the parent group", async () => {
            await openEditor();

            await expect(
                legacyTextInput("Additional Parent Group", dialog),
                "Changed parent group persists",
            ).toHaveValue(groups[1]);

            await expect(
                legacyTextInput("User path", dialog),
                "Changed user path persists",
            ).toHaveValue("sources/ldap-updated");

            await expect(
                legacyTextInput("Additional User DN", dialog),
                "Changed additional user DN persists",
            ).toHaveValue("ou=users");

            await selectSearchValue(
                legacyTextInput("Additional Parent Group", dialog),
                /---------/,
            );

            await click("Save Changes", "button", dialog);
            await expect(dialog, "Editor closes after clearing parent group").toBeHidden();
        });

        await test.step("Verify cleared parent group persists", async () => {
            await openEditor();

            await expect(
                legacyTextInput("Additional Parent Group", dialog),
                "Parent group remains cleared after reopening",
            ).toHaveValue("");
        });
    });
});
