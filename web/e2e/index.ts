/* eslint-disable react-hooks/rules-of-hooks */
import { DeepLocatorProxy, createLocatorProxy } from "#e2e/elements/proxy";
import { FormFixture } from "#e2e/fixtures/FormFixture";
import { ProvidersFixture } from "#e2e/fixtures/ProvidersFixture";
import { SessionFixture } from "#e2e/fixtures/SessionFixture";
import { UserLibraryFixture } from "#e2e/fixtures/UserLibraryFixture";
import { createOUIDNameEngine } from "#e2e/selectors/ouid";
import { ConsoleLogger } from "#logger/node";
import { test as base } from "@playwright/test";

export { expect } from "@playwright/test";

type TestIDLocatorProxy = DeepLocatorProxy<TestIDSelectorMap>;

interface E2EFixturesTestScope {
    /**
     * A proxy to retreive elements by test ID.
     *
     * ```ts
     * const $button = $.button;
     * ```
     */
    $: TestIDLocatorProxy;
    session: SessionFixture;
    providers: ProvidersFixture;
    userLibrary: UserLibraryFixture;
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
        await use(createLocatorProxy<TestIDSelectorMap>(page, "test-id"));
    },

    session: async ({ page }, use, { title }) => {
        await use(new SessionFixture(page, title));
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
