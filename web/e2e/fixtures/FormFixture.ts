import { PageFixture } from "#e2e/fixtures/PageFixture";
import { Locator, Page, expect } from "@playwright/test";

export class FormFixture extends PageFixture {
    static fixtureName = "Form";

    //#region Form Selectors

    /**
     * Set the value of a search select input.
     *
     * @param name The name of the search select element.
     * @param pattern The text to match against the search select entry.
     */
    public async selectSearchValue(
        name: string,
        pattern: string | RegExp,
        parent: Pick<Locator, "locator"> = this.page,
    ): Promise<void> {
        let control = parent.locator(`ak-search-select[name="${name}"]`);

        const found = await control.isVisible();

        if (!found) {
            control = parent.locator(`ak-search-select-ez[name="${name}"]`);
        }

        await expect(control, `Search select control (${name}) should be visible`).toBeVisible();

        if (!control) {
            throw new Error(`Unable to find an ak-search-select variant matching ${name}}`);
        }

        // Find the search select input control and activate it.
        const view = control.locator("ak-search-select-view");
        const input = view.locator('input[type="text"]');

        await input.scrollIntoViewIfNeeded();
        await input.click();

        const button = this.page
            // ---
            .locator(`div[data-managed-for*="${name}"]`)
            .locator("button", {
                hasText: pattern,
            });

        if (!button) {
            throw new Error(
                `Unable to find an ak-search-select entry matching ${name}:${pattern.toString()}`,
            );
        }

        await button.click();
        await this.page.keyboard.press("Tab");
        await control.blur();
    }

    public async selectAuthorizationFlow(
        parent: Pick<Locator, "locator"> = this.page,
        pattern: string | RegExp,
        name = "authorizationFlow",
    ) {
        return this.selectSearchValue(name, pattern, parent);
    }

    //#region Public Methods

    //#region Lifecycle

    constructor(page: Page, testName: string) {
        super({ page, testName });
    }

    //#endregion
}
