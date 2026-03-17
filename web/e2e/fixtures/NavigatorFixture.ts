import { PageFixture } from "#e2e/fixtures/PageFixture";

import { Page } from "@playwright/test";

export const GOOD_USERNAME = "test-admin@goauthentik.io";
export const GOOD_PASSWORD = "test-runner";

export const BAD_USERNAME = "bad-username@bad-login.io";
export const BAD_PASSWORD = "-this-is-a-bad-password-";

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
    public waitForPathname = async (to: string | URL): Promise<void> => {
        const expectedPathname = typeof to === "string" ? to : to.pathname;

        this.logger.info(`Waiting for URL to change to ${expectedPathname}`);

        await this.page.waitForURL(`**${expectedPathname}**`);

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
