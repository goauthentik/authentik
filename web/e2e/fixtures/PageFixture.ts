import { ConsoleLogger, FixtureLogger } from "#logger/node";

import { Page } from "@playwright/test";

export interface PageFixtureInit {
    page: Page;
    testName: string;
}

export abstract class PageFixture {
    /**
     * The name of the fixture.
     *
     * Used for logging.
     */
    static fixtureName: string;

    protected readonly logger: FixtureLogger;
    protected readonly page: Page;
    protected readonly testName: string;

    constructor({ page, testName }: PageFixtureInit) {
        this.page = page;
        this.testName = testName;

        const Constructor = this.constructor as typeof PageFixture;

        this.logger = ConsoleLogger.fixture(Constructor.fixtureName, this.testName);
    }
}
