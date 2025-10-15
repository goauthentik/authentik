/**
 * @file Playwright e2e test helpers.
 */

import { FormFixture } from "#e2e/fixtures/FormFixture";
import { NavigatorFixture } from "#e2e/fixtures/NavigatorFixture";
import { PointerFixture } from "#e2e/fixtures/PointerFixture";
import { SessionFixture } from "#e2e/fixtures/SessionFixture";

import { test as base } from "@playwright/test";

export { expect } from "@playwright/test";

/* eslint-disable react-hooks/rules-of-hooks */

interface E2EFixturesTestScope {
    navigator: NavigatorFixture;
    session: SessionFixture;
    pointer: PointerFixture;
    form: FormFixture;
}

interface E2EWorkerScope {
    selectorRegistration: void;
}

export const test = base.extend<E2EFixturesTestScope, E2EWorkerScope>({
    navigator: async ({ page }, use, { title }) => {
        await use(new NavigatorFixture(page, title));
    },

    session: async ({ page, navigator }, use, { title: testName }) => {
        await use(new SessionFixture({ page, testName, navigator }));
    },

    form: async ({ page }, use, { title }) => {
        await use(new FormFixture(page, title));
    },

    pointer: async ({ page }, use, { title: testName }) => {
        await use(new PointerFixture({ page, testName }));
    },
});
