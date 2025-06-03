import { Locator, Page } from "@playwright/test";

export class UserLibraryFixture {
    public static readonly pathname = "/if/user/#/library";

    public $pageHeading: Locator;

    constructor(public readonly page: Page) {
        this.$pageHeading = this.page.getByTestId("page-heading");
    }
}
