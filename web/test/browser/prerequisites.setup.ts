import { expect, test as setup } from "#e2e";

const IDENTIFICATION_STAGE_NAME = "default-authentication-identification";

// The availability check gates the rest, which log in through the default flow.
setup.describe.configure({ mode: "serial" });

setup("Web server availability", async ({ baseURL }) => {
    expect(baseURL, "Base URL is set").toBeTruthy();

    // The API can answer before the worker has applied the default blueprints, and until then
    // `/` redirects to an authentication flow that doesn't exist yet and 404s. Poll until the
    // whole redirect chain resolves.
    setup.setTimeout(120_000);

    await expect
        .poll(
            () =>
                fetch(baseURL!)
                    .then((res) => res.ok)
                    .catch(() => false),
            {
                message: `Web server should be serving the login flow on ${baseURL}`,
                timeout: 90_000,
            },
        )
        .toBe(true);
});

// The remember-me coverage in `101-session-lifecycle` needs this switch on, and it lives
// on the default identification stage — shared by every login in the suite. Enabling it
// here means it happens once, before any worker starts, rather than from a `beforeAll`
// that saves a flow stage while other workers are authenticating through it.
setup('Enable "Remember me on this device"', async ({ session, form, page }) => {
    await setup.step("Authenticate", () => session.login({ to: "/if/admin/flow/stages" }));

    const $stage = await setup.step("Find the identification stage", () =>
        form.search(IDENTIFICATION_STAGE_NAME),
    );

    await $stage.getByRole("button", { name: "Edit Stage" }).click();

    const dialog = page.getByRole("dialog", { name: "Edit Identification Stage" });

    await expect(dialog, "Edit modal opens").toBeVisible();

    await form.setInputCheck(`Enable "Remember me on this device"`, true, dialog);
    await dialog.getByRole("button", { name: "Save Changes" }).click();

    await expect(dialog, "Edit modal closes after save").toBeHidden();
});
