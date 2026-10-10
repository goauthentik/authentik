import { PageFixture } from "#e2e/fixtures/PageFixture";
import type { LocatorContext } from "#e2e/selectors/types";

import { expect, Locator, Page } from "@playwright/test";

export class FormFixture extends PageFixture {
    static fixtureName = "Form";

    //#region Selector Methods

    //#endregion

    //#region Field Methods

    /**
     * Locate a legacy input whose wrapper label is in a different shadow root.
     * Prefer accessible-name queries for controls with properly associated labels.
     */
    public legacyTextInput = (label: string, context: LocatorContext = this.page): Locator =>
        context
            .locator(`ak-form-element-horizontal[label=${JSON.stringify(label)}]`)
            .getByRole("textbox");

    /**
     * Set the value of a text input.
     *
     * @param fieldName The name of the form element.
     * @param value The value to set.
     */
    public findTextualInput = async (
        fieldName: string | RegExp,
        context: LocatorContext = this.page,
    ) => {
        const textbox = context.getByRole("textbox", { name: fieldName });
        const searchbox = context.getByRole("searchbox", { name: fieldName });
        const spinbutton = context.getByRole("spinbutton", { name: fieldName });

        // Comboboxes (e.g. the Query Language input) wrap an inner textbox.
        const comboboxTextbox = context
            .getByRole("combobox", { name: fieldName })
            .getByRole("textbox");

        const control = textbox.or(searchbox).or(spinbutton).or(comboboxTextbox);

        await expect(control, `Field (${fieldName}) should be visible`).toBeVisible();

        return control;
    };

    /**
     * Set the value of a text input.
     *
     * @param target The name of the form element.
     * @param value The value to set.
     */
    public fill = async (
        target: string | RegExp | Locator,
        value: string,
        context: LocatorContext = this.page,
    ): Promise<void> => {
        let control: Locator;

        if (typeof target === "string" || target instanceof RegExp) {
            control = await this.findTextualInput(target, context);
        } else {
            control = target;
        }

        await control.fill(value);
    };

    /**
     * Search for a row containing the given text.
     *
     * @returns A locator for the row entry matching the query.
     */
    public search = async (
        query: string,
        context: LocatorContext = this.page,
    ): Promise<Locator> => {
        // Scoped to `ak-table-search` rather than the whole page: tables render either a
        // plain searchbox or a query-language combobox, so the match has to stay
        // role-based — but pages that mount a wizard (e.g. providers) also carry the
        // dual-list-select search boxes for scopes, sources, and providers, which an
        // unscoped match picks up and then fails strict mode on.
        const searchInput = await this.findTextualInput(
            /search/i,
            context.locator("ak-table-search"),
        );

        // We have to wait for the user to appear in the table,
        // but several UI elements will be rendered asynchronously.
        // We attempt several times to find the user to avoid flakiness.

        const tries = 10;
        let found = false;

        for (let i = 0; i < tries; i++) {
            await this.fill(searchInput, query);
            await searchInput.press("Enter");

            const $rowEntry = context.getByRole("row", {
                name: query,
            });

            this.logger.info(`${i + 1}/${tries} Waiting for "${query}" to appear in the table`);

            found = await $rowEntry
                .waitFor({
                    timeout: 1500,
                })
                .then(() => true)
                .catch(() => false);

            if (found) {
                this.logger.info(`"${query}" found in the table`);

                return $rowEntry;
            }
        }

        throw new Error(`"${query}" not found in the table`);
    };

    /**
     * Set the value of a radio or checkbox input.
     *
     * @param fieldName The name of the form element.
     * @param value The value to set.
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

        const checkbox = control.getByRole("checkbox");
        const currentChecked = await checkbox.isChecked();

        if (currentChecked === value) {
            return;
        }

        // The wrapper also contains help text; clicking its center can miss the switch.
        await control.locator("label.pf-c-switch").click();

        await expect(checkbox, `Field (${fieldName}) has the requested state`).toBeChecked({
            checked: value,
        });
    };

    /**
     * Set the value of a radio or checkbox input.
     *
     * @param fieldName The name of the form element.
     * @param pattern The value to set.
     */
    public setRadio = async (
        groupName: string,
        fieldName: string,
        parent: LocatorContext = this.page,
    ): Promise<void> => {
        const group = parent.getByRole("radiogroup", { name: groupName });

        await expect(group, `Field "${groupName}" should be visible`).toBeVisible();
        const control = parent.getByRole("radio", { name: fieldName });

        await control.setChecked(true);
    };

    /**
     * Find a search select's combobox by its label.
     *
     * @param fieldLabel The accessible name of the search select.
     */
    public findSearchSelect = async (
        fieldLabel: string | RegExp,
        parent: LocatorContext = this.page,
    ): Promise<{ host: Locator; combobox: Locator }> => {
        const byName = (exact: boolean) =>
            parent.getByRole("combobox", { name: fieldLabel, exact });

        const exact = typeof fieldLabel === "string" && (await byName(true).count()) > 0;
        const combobox = byName(exact);

        await expect(
            combobox,
            `Search select control (${fieldLabel}) should be visible`,
        ).toBeVisible();

        const host = parent.locator("ak-search-select").filter({
            has: this.page.getByRole("combobox", { name: fieldLabel, exact }),
        });

        return { host, combobox };
    };

    /**
     * Choose an option in a search select.
     *
     * @param fieldLabel The accessible name of the search select.
     * @param pattern The option to choose. A string is also typed in to search for it.
     */
    public selectSearchValue = async (
        fieldLabel: string | RegExp,
        pattern: string | RegExp,
        parent: LocatorContext = this.page,
    ): Promise<void> => {
        const { host, combobox } = await this.findSearchSelect(fieldLabel, parent);

        await combobox.click();

        if (typeof pattern === "string") {
            await combobox.fill(pattern);
        }

        const option = host.getByRole("option", { name: pattern }).first();

        await expect(option, `Search select option (${pattern}) should be visible`).toBeVisible();

        await option.click();

        await expect(
            host.getByRole("listbox"),
            `Search select (${fieldLabel}) closes after choosing`,
        ).toBeHidden();
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
