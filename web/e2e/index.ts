/**
 * @file Playwright e2e test helpers.
 */

import { FormFixture } from "#e2e/fixtures/FormFixture";
import { PointerFixture } from "#e2e/fixtures/PointerFixture";
import { SessionFixture } from "#e2e/fixtures/SessionFixture";

import { test as base } from "@playwright/test";

export { expect } from "@playwright/test";

/* eslint-disable react-hooks/rules-of-hooks */

interface E2EFixturesTestScope {
    session: SessionFixture;
    pointer: PointerFixture;
    form: FormFixture;
}

interface E2EWorkerScope {
    selectorRegistration: void;
}

export const test = base.extend<E2EFixturesTestScope, E2EWorkerScope>({
    session: async ({ page }, use, { title }) => {
        await use(new SessionFixture(page, title));
    },

    form: async ({ page }, use, { title }) => {
        await use(new FormFixture(page, title));
    },

    pointer: async ({ page }, use, { title }) => {
        await use(new PointerFixture({ page, testName: title }));
    },
});
