import { PageFixture } from "#e2e/fixtures/PageFixture";
import { Locator, Page, expect } from "@playwright/test";
import { kebabCase } from "change-case";

export class LandmarksFixture extends PageFixture {
    static fixtureName = "Landmarks";

    //#region Page Selectors

    public $pageNavbarHeading = this.page.getByTestId("page-navbar-heading");

    //#endregion

    //#region Form Selectors

    /**
     * Set the value of a search select input.
     *
     * @param name The name of the search select element.
     * @param pattern The text to match against the search select entry.
     */
    public async selectSearchValue(
        parent: Locator,
        name: string,
        pattern: string | RegExp,
    ): Promise<void> {
        let control = parent.locator(`ak-search-select[name="${name}"]`);

        const found = await control.isVisible();

        if (!found) {
            control = parent.locator(`ak-search-select-ez[name="${name}"]`);
        }

        await expect(control).toBeVisible();

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

    //#region Public Methods

    /**
     * Find an element by its dataset attribute.
     */
    public findElementByDataset(propertyName: string, value: string) {
        return this.page.locator(`[data-${kebabCase(propertyName)}="${value}"]`);
    }

    /**
     * Find an OUID component by name.
     */
    public findOUIDComponent(componentName: string) {
        return this.findElementByDataset("ouid-component-name", componentName);
    }

    //#region Lifecycle

    constructor(page: Page, testName: string) {
        super({ page, testName });
    }

    //#endregion
}
