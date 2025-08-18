import { expect, test } from "#e2e";

test.describe("JSX Rendering", () => {
    test("Simple static markup can be rendered", async ({ page, render }) => {
        await render(
            // @ts-ignore - testing
            <p style={{ color: "red", fontSize: "12px" }}>Hello World</p>,
        );

        await expect(page.getByText("Test 123")).toBeVisible();
    });
});
