import { ChildConsoleLogger, ConsoleLogger } from "#logger/node";
import { Locator, Page } from "@playwright/test";

export class LandmarksFixture {
    #logger: ChildConsoleLogger;

    //#region Selectors

    public $pageHeading: Locator;
    //#endregion

    constructor(
        public readonly page: Page,
        testName: string,
    ) {
        this.#logger = ConsoleLogger.child(
            { name: "Landmarks" },
            {
                msgPrefix: `[${testName}] `,
            },
        );

        this.$pageHeading = this.page.getByTestId("page-heading");

        this.#logger.info("Landmarks Fixture created");
    }
}
