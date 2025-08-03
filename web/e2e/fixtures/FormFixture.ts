import { PageFixture } from "#e2e/fixtures/PageFixture";
import type { LocatorContext } from "#e2e/selectors/types";

import { expect, Page } from "@playwright/test";

export class FormFixture extends PageFixture {
    static fixtureName = "Form";

    //#region Selector Methods

    //#endregion

    //#region Field Methods

    /**
     * Set the value of a text input.
     *
     * @param fieldName The name of the form element.
     * @param value the value to set.
     */
    public fill = async (
        fieldName: string,
        value: string,
        parent: LocatorContext = this.page,
    ): Promise<void> => {
        const control = parent
            .getByRole("textbox", {
                name: fieldName,
            })
            .or(
                parent.getByRole("spinbutton", {
                    name: fieldName,
                }),
            )
            .first();

        await expect(control, `Field (${fieldName}) should be visible`).toBeVisible();

        await control.fill(value);
    };

    /**
     * Set the value of a radio or checkbox input.
     *
     * @param fieldName The name of the form element.
     * @param value the value to set.
     */
    public setInputCheck = async (
        fieldName: string,
        value: boolean = true,
        parent: LocatorContext = this.page,
    ): Promise<void> => {
        const control = parent.locator("ak-switch-input", {
            hasText: fieldName,
        });

        await control.scrollIntoViewIfNeeded();

        await expect(control, `Field (${fieldName}) should be visible`).toBeVisible();

        const currentChecked = await control
            .getAttribute("checked")
            .then((value) => value !== null);

        if (currentChecked === value) {
            return;
        }

        await control.click();
    };

    /**
     * Set the value of a radio or checkbox input.
     *
     * @param fieldName The name of the form element.
     * @param pattern the value to set.
     */
    public setRadio = async (
        groupName: string,
        fieldName: string,
        parent: LocatorContext = this.page,
    ): Promise<void> => {
        const group = parent.getByRole("group", { name: groupName });

        await expect(group, `Field "${groupName}" should be visible`).toBeVisible();
        const control = parent.getByRole("radio", { name: fieldName });

        await control.setChecked(true, {
            force: true,
        });
    };

    /**
     * Set the value of a search select input.
     *
     * @param fieldLabel The name of the search select element.
     * @param pattern The text to match against the search select entry.
     */
    public selectSearchValue = async (
        fieldLabel: string,
        pattern: string | RegExp,
        parent: LocatorContext = this.page,
    ): Promise<void> => {
        const control = parent.getByRole("textbox", { name: fieldLabel });

        await expect(
            control,
            `Search select control (${fieldLabel}) should be visible`,
        ).toBeVisible();

        const fieldName = await control.getAttribute("name");

        if (!fieldName) {
            throw new Error(`Unable to find name attribute on search select (${fieldLabel})`);
        }

        // Find the search select input control and activate it.
        await control.click();

        const button = this.page
            // ---
            .locator(`div[data-managed-for*="${fieldName}"] button`, {
                hasText: pattern,
            });

        if (!button) {
            throw new Error(
                `Unable to find an ak-search-select entry matching ${fieldLabel}:${pattern.toString()}`,
            );
        }

        await button.click();
        await this.page.keyboard.press("Tab");
        await control.blur();
    };

    public setFormGroup = async (
        pattern: string | RegExp,
        value: boolean = true,
        parent: LocatorContext = this.page,
    ) => {
        const control = parent
            .locator("ak-form-group", {
                hasText: pattern,
            })
            .first();

        const currentOpen = await control.getAttribute("open").then((value) => value !== null);

        if (currentOpen === value) {
            this.logger.debug(`Form group ${pattern} is already ${value ? "open" : "closed"}`);
            return;
        }

        this.logger.debug(`Toggling form group ${pattern} to ${value ? "open" : "closed"}`);

        await control.click();

        if (value) {
            await expect(control).toHaveAttribute("open");
        } else {
            await expect(control).not.toHaveAttribute("open");
        }
    };

    //#endregion

    //#region Lifecycle

    constructor(page: Page, testName: string) {
        super({ page, testName });
    }

    //#endregion
}
