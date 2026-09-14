import { PageFixture } from "#e2e/fixtures/PageFixture";

import { expect, Locator } from "@playwright/test";

/**
 * The header account switcher (`ak-user-switcher`), which owns both the multi-account
 * entries and the sign-out affordance in the User and Admin interfaces.
 */
export class UserSwitcherFixture extends PageFixture {
    static fixtureName = "UserSwitcher";

    //#region Selectors

    public $switcher = this.page.locator("ak-user-switcher");

    public $toggle = this.$switcher.getByRole("button", { name: "Switch user" });

    public $addUser = this.$switcher.getByRole("menuitem", { name: "Add another user" });

    /**
     * Signs the active account out. Rendered unconditionally, which makes it the
     * sentinel for "the menu is open".
     */
    public $signOut = this.$switcher.getByRole("menuitem", { name: "Sign out current user" });

    /**
     * The menu entry for a single account.
     *
     * Entries are labelled with the account's display name and email, so an email
     * pattern identifies one unambiguously under any `UserDisplay` setting.
     */
    public entry = (pattern: string | RegExp): Locator =>
        this.$switcher.getByRole("menuitem", { name: pattern });

    //#endregion

    //#region Specific interactions

    /**
     * Open the menu, tolerating the session request settling mid-flight.
     *
     * `ak-dropdown` hides the menu from `connectedCallback`, so every re-render of
     * `ak-user-switcher` that rebuilds the dropdown subtree closes an already-open menu.
     * On a freshly loaded page the session response lands right about then, so a single
     * toggle click is not reliably enough to leave the menu open.
     */
    public open = async (): Promise<void> => {
        this.logger.info("Opening the account switcher...");

        await expect(this.$toggle, "Switcher toggle is visible").toBeVisible({ timeout: 10_000 });

        await expect(async () => {
            if (await this.$signOut.isHidden()) {
                await this.$toggle.click();
            }

            await expect(this.$signOut, "Switcher menu is open").toBeVisible({ timeout: 1_000 });
        }).toPass({ timeout: 20_000 });
    };

    /**
     * Open the menu and activate one of its entries.
     *
     * Entries cannot be asserted on before the menu is open: the closed `<menu>` carries
     * `hidden`, which drops its whole subtree from the accessibility tree, so `menuitem`
     * queries match nothing at all. Retrying around both the open and the click also
     * absorbs entries that arrive with a late session response.
     */
    public select = async (target: Locator): Promise<void> => {
        await expect(async () => {
            await this.open();

            await target.click({ timeout: 2_000 });
        }).toPass({ timeout: 25_000 });
    };

    //#endregion
}
