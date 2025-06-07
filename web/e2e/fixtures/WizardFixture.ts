import { PageFixture } from "#e2e/fixtures/PageFixture";
import { Page, expect } from "@playwright/test";

export class WizardFixture extends PageFixture {
    static fixtureName = "Wizard";

    //#region Page Selectors

    public $heading = this.page.getByTestId("wizard-heading");
    public $navigationPrevious = this.page.getByTestId("wizard-navigation-previous");
    public $navigationNext = this.page.getByTestId("wizard-navigation-next");
    public $navigationAbort = this.page.getByTestId("wizard-navigation-abort");
    public $navigationCancel = this.page.getByTestId("wizard-navigation-cancel");

    //#endregion

    //#region Navigation

    public async previousStep() {
        await expect(
            this.$navigationPrevious,
            "Wizard can navigate to previous step",
        ).toBeEnabled();

        await this.$navigationPrevious.click();
    }

    public async nextStep() {
        await expect(this.$navigationNext, "Wizard can navigate to next step").toBeEnabled();

        await this.$navigationNext.click();
    }

    public async abort() {
        await this.$navigationAbort.click();
    }

    public async cancel() {
        await this.$navigationCancel.click();
    }

    //#endregion

    //#region Public Methods

    public async assertHidden() {
        return expect(this.$heading, "Wizard should be hidden").toBeHidden();
    }

    public async assertVisible() {
        return expect(this.$heading, "Wizard should be visible").toBeVisible();
    }

    //#region Lifecycle

    constructor(page: Page, testName: string) {
        super({ page, testName });
    }

    //#endregion
}
