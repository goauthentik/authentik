import type { LicenseMixin } from "#elements/mixins/license";

import { PageFixture } from "#e2e/fixtures/PageFixture";

import { expect } from "@playwright/test";

export class LicenseFixture extends PageFixture {
    static fixtureName = "License";

    public async isAvailable(): Promise<boolean> {
        const $interface = this.page.locator("ak-interface-admin, ak-interface-user");

        await expect
            .poll(
                () =>
                    $interface.evaluate((element: HTMLElement & LicenseMixin) =>
                        Boolean(element.licenseSummary),
                    ),
                { message: "License summary has loaded" },
            )
            .toBe(true);

        return $interface.evaluate(
            (element: HTMLElement & LicenseMixin) => element.hasEnterpriseLicense,
        );
    }
}
