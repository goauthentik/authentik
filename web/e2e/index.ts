/* eslint-disable react-hooks/rules-of-hooks */
import { LandmarksFixture } from "#e2e/fixtures/landmarks";
import { ProvidersListFixture } from "#e2e/fixtures/providers-list";
import { SessionFixture } from "#e2e/fixtures/session";
import { UserLibraryFixture } from "#e2e/fixtures/user-library";
import { test as base } from "@playwright/test";

import { TodoPage } from "./todo-page.js";

export { expect } from "@playwright/test";

type E2EFixtures = {
    session: SessionFixture;
    providersList: ProvidersListFixture;
    userLibrary: UserLibraryFixture;
    landmarks: LandmarksFixture;
};

export const test = base.extend<E2EFixtures>({
    landmarks: async ({ page }, use, { title }) => {
        await use(new LandmarksFixture(page, title));
    },

    session: async ({ page }, use, { title }) => {
        await use(new SessionFixture(page, title));
    },

    userLibrary: async ({ page }, use) => {
        await use(new UserLibraryFixture(page));
    },
});
