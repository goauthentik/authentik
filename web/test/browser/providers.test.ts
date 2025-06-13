import { expect, test } from "#e2e";
import { ProvidersFixture } from "#e2e/fixtures/ProvidersFixture";
import { createRandomName } from "#e2e/utils/generators";
import { P, series } from "#e2e/utils/runner";
import { ConsoleLogger } from "#logger/node";
import { IDGenerator } from "@goauthentik/core/id";

test.describe("Configure Providers", () => {
    const providerNames = new Map<string, string>();

    //#region Lifecycle

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
    });

    test.afterEach(async ({ providers }, { testId }) => {
        const { $providerList } = providers;

        const providerName = providerNames.get(testId)!;

        const searchInput = $providerList
            .getByRole("search")
            .getByPlaceholder("Search for providers");

        await searchInput.fill(providerName);

        //#region Confirm provider

        // We have to wait for the provider to appear in the table,
        // but several UI elements will be rendered asynchronously.
        // We attempt several times to find the provider to avoid flakiness.

        const tries = 10;
        let found = false;

        for (let i = 0; i < tries; i++) {
            await searchInput.press("Enter");
            await searchInput.blur();

            const $table = $providerList.getByRole("row", {
                name: providerName,
            });

            ConsoleLogger.info(
                `${i + 1}/${tries} Waiting for provider ${providerName} to appear in the table`,
            );

            found = await $table
                .waitFor({
                    timeout: 1500,
                })
                .then(() => true)
                .catch(() => false);

            if (found) {
                ConsoleLogger.info(`Provider ${providerName} found in the table`);
                break;
            }
        }

        if (!found) {
            throw new Error(`Provider ${providerName} not found in the table`);
        }

        //#endregion
    });

    //#endregion

    //#region OAuth2

    test("Should configure a simple OAuth2 Provider", async ({
        $,
        page,
        providers,
        form,
    }, testInfo) => {
        const { wizard } = $;

        await page.locator("ouid=oauth2provider").click();

        await wizard.navigation.next.click();

        const providerName = providerNames.get(testInfo.testId)!;
        const $providerForm = providers.locateProviderForm("oauth2");

        await form.fillTextField("name", providerName, $providerForm);

        await form.selectSearchValue(
            "Authorization flow",
            /default-provider-authorization-explicit-consent/,
        );

        await wizard.navigation.next.click();
    });

    test("Should configure a complete OAuth2 Provider", async ({
        $,
        page,
        providers,
        form,
    }, testInfo) => {
        const { wizard } = $;

        const { $providerList } = providers;

        await page.locator("ouid=oauth2provider").click();

        await wizard.navigation.next.click();

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

        await series(
            P(form.selectSearchValue, "Signing Key", /authentik Self-signed Certificate/),
            P(form.selectSearchValue, "Encryption Key", /authentik Self-signed Certificate/),
            P(form.setFormGroup, "Advanced flow settings", true),
            P(form.selectSearchValue, "Authentication flow", /default-source-authentication/),
            P(form.selectSearchValue, "Invalidation flow", /default-invalidation-flow/),
            P(form.setFormGroup, "Advanced protocol settings", true),
            P(form.fillTextField, "Access code validity", "minutes=2"),
            P(form.fillTextField, "Access token validity", "minutes=10"),
            P(form.fillTextField, "Refresh token validity", "days=40"),
            P(form.setInputCheck, "Include claims in id_token", false),
            P(form.setRadio, "Subject mode", "Based on the User's username"),
            P(form.setRadio, "Issuer mode", "Same identifier is used for all providers"),
            P(form.setFormGroup, "Machine-to-Machine authentication settings", true),
            P(wizard.navigation.next.click),
        );
    });

    //#endregion

    //#region LDAP

    test("Should configure a complete LDAP Provider", async ({
        $,
        page,
        providers,
        form,
    }, testInfo) => {
        const { wizard } = $;

        const $providerForm = providers.locateProviderForm("ldap");

        await expect(
            $providerForm,
            "LDAP Provider Form is not visible until next is clicked",
        ).toBeHidden();

        await page.locator("ouid=ldapprovider").click();

        await wizard.navigation.next.click();

        await expect(
            $providerForm,
            "LDAP Provider Form is visible after next is clicked",
        ).toBeVisible();

        const providerName = providerNames.get(testInfo.testId)!;

        await series(
            P(form.fillTextField, "name", providerName, $providerForm),
            P(form.setFormGroup, "Flow settings", true),
            P(form.setFormGroup, "Protocol settings", true),
            P(form.selectSearchValue, "Bind flow", /default-authentication-flow/),
            P(form.fillTextField, "Base DN", "DC=ldap-2,DC=goauthentik,DC=io"),
            P(form.selectSearchValue, "Certificate", /authentik Self-signed Certificate/),
            P(form.fillTextField, "TLS Server name", "goauthentik.io"),
            P(form.fillNumericField, "UID start number", "2001"),
            P(form.fillNumericField, "GID start number", "4001"),
            P(form.setRadio, "Search mode", "Direct querying"),
            P(form.setRadio, "Bind mode", "Direct binding"),
            P(form.setInputCheck, "MFA Support", false),
            P(wizard.navigation.next.click),
        );
    });

    //#endregion
});
