/* eslint-disable react-hooks/rules-of-hooks */
import { FormFixture } from "#e2e/fixtures/FormFixture";
import { LandmarksFixture } from "#e2e/fixtures/LandmarksFixture";
import { ProvidersFixture } from "#e2e/fixtures/ProvidersFixture";
import { SessionFixture } from "#e2e/fixtures/SessionFixture";
import { UserLibraryFixture } from "#e2e/fixtures/UserLibraryFixture";
import { WizardFixture } from "#e2e/fixtures/WizardFixture";
import { test as base } from "@playwright/test";

export { expect } from "@playwright/test";

interface E2EFixtures {
    landmarks: LandmarksFixture;
    session: SessionFixture;
    providers: ProvidersFixture;
    userLibrary: UserLibraryFixture;
    wizard: WizardFixture;
    form: FormFixture;
}

export const test = base.extend<E2EFixtures>({
    landmarks: async ({ page }, use, { title }) => {
        await use(new LandmarksFixture(page, title));
    },

    session: async ({ page }, use, { title }) => {
        await use(new SessionFixture(page, title));
    },

    wizard: async ({ page }, use, { title }) => {
        await use(new WizardFixture(page, title));
    },

    form: async ({ page }, use, { title }) => {
        await use(new FormFixture(page, title));
    },

    providers: async ({ page }, use, { title }) => {
        await use(new ProvidersFixture(page, title));
    },

    userLibrary: async ({ page }, use, { title }) => {
        await use(new UserLibraryFixture(page, title));
    },
});
