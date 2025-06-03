import { ChildConsoleLogger, ConsoleLogger } from "#logger/node";
import { Locator, Page } from "@playwright/test";

export abstract class ProvidersListFixture {
    static pathname = "/if/admin/#/core/providers";
    #logger: ChildConsoleLogger;

    //#region Selectors

    public $newProviderButton: Locator;

    public $searchInput: Locator;

    public $searchButton: Locator;

    //#endregion

    constructor(
        public readonly page: Page,
        testName: string,
    ) {
        this.#logger = ConsoleLogger.child(
            { name: "Providers" },
            {
                msgPrefix: `[${testName}] `,
            },
        );

        this.$newProviderButton = this.page.getByTestId("new-provider-button");
        this.$searchInput = this.page.getByTestId("table-search-input");
        this.$searchButton = this.page.getByTestId("table-search-submit");

        this.#logger.info("Providers Fixture created");
    }

    //#region Navigation

    public toProvidersListPage() {
        return this.page.goto(ProvidersListFixture.pathname);
    }

    //#endregion
}
