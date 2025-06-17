/* eslint-disable react-hooks/rules-of-hooks */
import { DeepLocatorProxy, createLocatorProxy } from "#e2e/elements/proxy";
import { FormFixture } from "#e2e/fixtures/FormFixture";
import { PointerFixture } from "#e2e/fixtures/PointerFixture";
import { SessionFixture } from "#e2e/fixtures/SessionFixture";
import { createOUIDNameEngine } from "#e2e/selectors/ouid";
import { type Page, test as base } from "@playwright/test";

export { expect } from "@playwright/test";

type TestIDLocatorProxy = DeepLocatorProxy<TestIDSelectorMap>;

interface E2EFixturesTestScope {
    /**
     * A proxy to retrieve elements by test ID.
     *
     * ```ts
     * const $button = $.button;
     * ```
     */
    $: TestIDLocatorProxy;
    session: SessionFixture;
    pointer: PointerFixture;
    form: FormFixture;
}

interface E2EWorkerScope {
    selectorRegistration: void;
}

export const test = base.extend<E2EFixturesTestScope, E2EWorkerScope>({
    selectorRegistration: [
        async ({ playwright }, use) => {
            await playwright.selectors.register("ouid", createOUIDNameEngine);
            await use();
        },
        { auto: true, scope: "worker" },
    ],

    $: async ({ page }, use) => {
        await use(createLocatorProxy<TestIDSelectorMap>(page));
    },

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
