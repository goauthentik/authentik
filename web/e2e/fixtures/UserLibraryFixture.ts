import { PageFixture } from "#e2e/fixtures/PageFixture";
import { Page } from "@playwright/test";

export class UserLibraryFixture extends PageFixture {
    public static fixtureName = "UserLibrary";
    public static readonly pathname = "/if/user/#/library";

    public $pageHeading = this.page.getByTestId("page-heading");

    constructor(page: Page, testName: string) {
        super({ page, testName });
    }
}
