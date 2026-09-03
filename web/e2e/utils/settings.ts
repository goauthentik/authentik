import { FormFixture } from "#e2e/fixtures/FormFixture";
import { NavigatorFixture } from "#e2e/fixtures/NavigatorFixture";
import { PointerFixture } from "#e2e/fixtures/PointerFixture";
import { SessionFixture } from "#e2e/fixtures/SessionFixture";

import { expect, Page } from "@playwright/test";

// The `/admin/settings` route mounted under the `/if/admin/` interface.
const SETTINGS_PATHNAME = "/if/admin/admin/settings";

/**
 * Toggle one of the instance feature flags (the "Flags" group on the admin settings page)
 * through the UI, and wait for the save to be confirmed.
 *
 * Written to run outside a test body — e.g. from `beforeAll`/`afterAll`, where the per-test
 * fixtures aren't injected — so it constructs the handful of fixtures it needs against a
 * caller-supplied page and drives the same UI a human would. Asserting the success toast
 * (rather than the settings network response) keeps this on the UI, and guarantees the write
 * has landed before the caller closes the page.
 *
 * @param page A page to drive; authenticates as the default admin if not already signed in.
 * @param flagLabel The visible label of the flag's switch, e.g. "Continuous Login".
 * @param enabled Whether the flag should end up on.
 */
export async function setInstanceFlag(
    page: Page,
    flagLabel: string,
    enabled: boolean,
): Promise<void> {
    const testName = `set-instance-flag:${flagLabel}`;
    const navigator = new NavigatorFixture(page, testName);
    const session = new SessionFixture({ page, testName, navigator });
    const form = new FormFixture(page, testName);
    const pointer = new PointerFixture({ page, testName });

    await session.login({ to: SETTINGS_PATHNAME });

    await form.setFormGroup(/Flags/, true);
    await form.setInputCheck(flagLabel, enabled);

    await pointer.click("Save changes");

    await expect(
        page.getByText("Successfully updated settings."),
        `Settings save is confirmed after toggling "${flagLabel}"`,
    ).toBeVisible();
}
