import { PageFixture } from "#e2e/fixtures/PageFixture";

import { Page } from "@playwright/test";

export interface LoginInit {
    username?: string;
    password?: string;
    to?: URL | string;
}

export class NavigatorFixture extends PageFixture {
    static fixtureName = "Navigator";

    constructor(page: Page, testName: string) {
        super({ page, testName });
    }

    /**
     * Wait for the current page to navigate to the given pathname.
     *
     * This method is useful to verify that a navigation has completed after an action
     * automatically updates the URL, such as form submissions or link clicks.
     *
     * @see {@linkcode navigate} for navigation.
     *
     * @param to The pathname or URL to wait for.
     */
    public waitForPathname = async (
        to: string | URL,
        options?: Parameters<Page["waitForURL"]>[1],
    ): Promise<void> => {
        const expectedPathname = typeof to === "string" ? to : to.pathname;

        this.logger.info(`Waiting for URL to change to ${expectedPathname}`);

        await this.page.waitForURL(`**${expectedPathname}**`, options);

        this.logger.info(`URL changed to ${this.page.url()}`);
    };

    /**
     * Wait for the current page to navigate away from the given pathname.
     *
     * Use this when the destination isn't known ahead of time, such as a login whose
     * post-submit redirect lands on whichever interface the user defaults to. Waiting
     * on a known pathname would match the page we're already on and resolve before the
     * navigation lands.
     *
     * @see {@linkcode waitForPathname} when the destination is known.
     *
     * @param from The pathname or URL to wait for the page to leave.
     */
    public waitForPathnameChange = async (
        from: string | URL,
        options?: Parameters<Page["waitForURL"]>[1],
    ): Promise<void> => {
        const currentPathname = typeof from === "string" ? from : from.pathname;

        this.logger.info(`Waiting for URL to change away from ${currentPathname}`);

        await this.page.waitForURL((url) => url.pathname !== currentPathname, options);

        this.logger.info(`URL changed to ${this.page.url()}`);
    };

    /**
     * Navigate to the given URL or pathname, and wait for the navigation to complete.
     */
    public navigate = async (to: URL | string | null | undefined): Promise<void> => {
        if (!to) {
            throw new TypeError("No URL or pathname given to navigate to.");
        }

        await this.page.goto(to.toString());

        await this.waitForPathname(to);
    };
}
