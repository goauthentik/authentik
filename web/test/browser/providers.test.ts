import { expect, test } from "#e2e";
import { ProvidersFixture } from "#e2e/fixtures/ProvidersFixture";
import { createRandomName } from "#e2e/utils/generators";
import { IDGenerator } from "@goauthentik/core/id";

test.describe("Configure OAuth2 Providers", () => {
    const providerNames = new Map<string, string>();

    test.beforeEach(async ({ $, page, session, providers }, { testId }) => {
        const { wizard } = $;

        const seed = IDGenerator.randomID(6);
        const providerName = `${createRandomName({ seed })} (${seed})`;

        providerNames.set(testId, providerName);

        await session.login({
            to: ProvidersFixture.pathname,
        });

        await expect(wizard.heading.$, "Wizard is initially closed").toBeHidden();

        await providers.$providerList.getByLabel("New Provider").click();

        await expect(wizard.heading.$, "Wizard opens after clicking on New Provider").toBeVisible();

        await expect(page.locator("ak-wizard-page-type-create")).toBeVisible();

        await wizard.navigation.next.expect.toBeDisabled();

        const $ouidComponent = page.locator("ouid=oauth2provider");

        await $ouidComponent.click();

        await wizard.navigation.next.click();
    });

    test.afterEach(async ({ $, providers, page }, { testId }) => {
        // const { wizard } = $;
        const { $providerList } = providers;

        const providerName = providerNames.get(testId)!;

        // await expect(wizard.heading.$, "Wizard has closed").toBeHidden({
        //     timeout: 1500,
        // });

        const searchInput = $providerList
            .getByRole("search")
            .getByPlaceholder("Search for providers");

        await page.waitForTimeout(1000);

        await searchInput.fill(providerName);
        await searchInput.focus();
        await searchInput.press("Enter", { delay: 200 });
        await searchInput.press("Enter", { delay: 200 });

        await searchInput.blur();

        // const response = page.waitForResponse((response) => {
        //     const url = new URL(response.url());
        //     return (
        //         url.pathname.startsWith("/api/v3/providers/all/") &&
        //         url.searchParams.get("search") === providerName
        //     );
        // });

        // // await $providerList
        // //     .getByRole("search")
        // //     .getByRole("button", { name: "Search", exact: true })
        // //     .click({
        // //         force: true,
        // //     });

        // await response;

        await expect(
            $providerList.getByText(providerName),
            `Provider "${providerName}" should be visible`,
        ).toBeVisible({
            timeout: 1500,
        });
    });

    test("Should configure a simple OAuth2 Application", async ({
        $,
        providers,
        form,
    }, testInfo) => {
        const { wizard } = $;

        const providerName = providerNames.get(testInfo.testId)!;
        const $providerForm = providers.locateProviderForm("oauth2");

        const nameField = $providerForm.getByRole("textbox", {
            name: "name",
        });

        await expect(nameField).toBeVisible();

        await nameField.fill(providerName);

        await form.selectSearchValue(
            "Authorization flow",
            /default-provider-authorization-explicit-consent/,
        );

        await wizard.navigation.next.click();
    });

    test("Should configure a complete OAuth2 Application", async ({
        $,
        page,
        providers,
        form,
    }, testInfo) => {
        const { wizard } = $;

        const { $providerList } = providers;
        const $providerForm = providers.locateProviderForm("oauth2");

        const providerName = providerNames.get(testInfo.testId)!;

        await expect($providerList.getByText(providerName)).toBeHidden();

        await form.fillTextField("name", providerName, $providerForm);

        await form.selectSearchValue(
            "Authorization flow",
            /default-provider-authorization-explicit-consent/,
        );

        await form.setFormGroup("Protocol settings", true);

        await form.setRadio("Client Type", "Public");

        const $clientSecretInput = $providerForm.getByRole("textbox", { name: "Client Secret" });

        await expect(
            $clientSecretInput,
            "Client Secret should be hidden when Client Type is Public",
        ).toBeHidden();

        await form.setRadio("Client Type", "Confidential");

        await expect(
            $clientSecretInput,
            "Client Secret should be visible when Client Type is Confidential",
        ).toBeVisible();

        await form.selectSearchValue("Signing Key", /authentik Self-signed Certificate/);
        await form.selectSearchValue("Encryption Key", /authentik Self-signed Certificate/);

        await form.setFormGroup("Advanced flow settings", true);

        await form.selectSearchValue("Authentication flow", /default-source-authentication/);
        await form.selectSearchValue("Invalidation flow", /default-invalidation-flow/);

        await form.setFormGroup("Advanced protocol settings", true);

        await form.fillTextField("Access code validity", "minutes=2");
        await form.fillTextField("Access token validity", "minutes=10");
        await form.fillTextField("Refresh token validity", "days=40");

        await form.setInputCheck("Include claims in id_token", false);
        await form.setRadio("Subject mode", "Based on the User's username");

        await form.setRadio("Issuer mode", "Same identifier is used for all providers");

        await form.setFormGroup("Machine-to-Machine authentication settings", true);

        const request = page.waitForRequest((request) => {
            const url = new URL(request.url());
            return url.pathname.startsWith("/api/v3/providers/") && request.method() === "GET";
        });

        const response = page.waitForResponse((response) => {
            return response.url().includes("/api/v3/providers/") && response.ok();
        });

        await wizard.navigation.next.click();

        await request;
        await response;
    });
});
