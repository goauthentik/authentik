import { expect, test } from "#e2e";

test.describe("Applications", () => {
    test("Slug auto-sync matches backend slugify rules", async ({ page, session, form }) => {
        await session.login({
            to: "/if/admin/#/core/applications",
        });

        await page.getByRole("button", { name: "Create", exact: true }).click();

        const dialog = page.getByRole("dialog", { name: "Create Application" });
        await expect(dialog).toBeVisible();

        const slugField = dialog.getByRole("textbox", { name: "Slug" });

        const cases: Array<[string, string]> = [
            ["OAuth", "oauth"],
            ["UARRRggggg", "uarrrggggg"],
            ["My Application", "my-application"],
            ["  --Hello   World--  ", "hello-world"],
            ["Tést Äpp", "test-app"],
            ["___My_App___", "my_app"],
            ["A&B*C", "abc"],
            ["Hi😀There", "hithere"],
        ];

        for (const [name, expectedSlug] of cases) {
            await form.fill("Name", name, dialog);
            await expect(slugField).toHaveValue(expectedSlug);
        }
    });
});
