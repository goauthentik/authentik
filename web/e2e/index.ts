/**
 * @file Playwright e2e test helpers.
 */

import { CaptchaFixture } from "#e2e/fixtures/CaptchaFixture";
import { FormFixture } from "#e2e/fixtures/FormFixture";
import { LicenseFixture } from "#e2e/fixtures/LicenseFixture";
import { NavigatorFixture } from "#e2e/fixtures/NavigatorFixture";
import { PasskeyFixture } from "#e2e/fixtures/PasskeyFixture";
import { PointerFixture } from "#e2e/fixtures/PointerFixture";
import { SessionFixture } from "#e2e/fixtures/SessionFixture";
import { UserSwitcherFixture } from "#e2e/fixtures/UserSwitcherFixture";

import { test as base } from "@playwright/test";

export { expect } from "@playwright/test";

/* eslint-disable react-hooks/rules-of-hooks */

interface E2EFixturesTestScope {
    license: LicenseFixture;
    navigator: NavigatorFixture;
    session: SessionFixture;
    pointer: PointerFixture;
    form: FormFixture;
    passkey: PasskeyFixture;
    captcha: CaptchaFixture;
    switcher: UserSwitcherFixture;
}

interface E2EWorkerScope {
    selectorRegistration: void;
}

export const test = base.extend<E2EFixturesTestScope, E2EWorkerScope>({
    license: async ({ page }, use, { title: testName }) => {
        await use(new LicenseFixture({ page, testName }));
    },

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

    captcha: async ({ page, form, pointer, navigator }, use, { title: testName }) => {
        await use(new CaptchaFixture({ page, testName, form, pointer, navigator }));
    },

    passkey: async ({ page, context }, use, { title: testName }) => {
        await use(new PasskeyFixture({ page, testName, context }));
    },

    switcher: async ({ page }, use, { title: testName }) => {
        await use(new UserSwitcherFixture({ page, testName }));
    },
});
