import { expect, test } from "#e2e";
import { ProvidersFixture } from "#e2e/fixtures/ProvidersFixture";
import { IDGenerator } from "@goauthentik/core/id";

function formatProviderName(providerName = "Test Provider") {
    return `${providerName} (${IDGenerator.randomID()})`;
}

test.describe("Configure OAuth2 Providers", () => {
    test.beforeEach(async ({ $, page, session }) => {
        const { wizard } = $;

        await session.login({
            to: ProvidersFixture.pathname,
        });

        await wizard.heading.expect.toBeHidden();

        await $.provider.new.click();

        await wizard.heading.expect.toBeVisible();
        await expect(page.locator("ak-wizard-page-type-create")).toBeVisible();

        await wizard.navigation.next.expect.toBeDisabled();

        const $ouidComponent = page.locator("ouid=oauth2provider");

        await $ouidComponent.click();

        await wizard.navigation.next.click();
    });

    test("Should configure a simple OAuth2 Application", async ({ $, providers, form }) => {
        const { wizard } = $;

        const $providerForm = providers.locateProviderForm("oauth2");

        const providerName = formatProviderName("Simple OAuth2");

        const nameField = $providerForm.getByRole("textbox", {
            name: "name",
        });

        await expect(nameField).toBeVisible();

        await nameField.fill(providerName);

        await form.selectAuthorizationFlow(
            $providerForm,
            /default-provider-authorization-explicit-consent/,
        );

        await wizard.navigation.next.click();
    });

    test("Should configure a complete OAuth2 Application", async ({ $, providers, form }) => {
        const { wizard } = $;

        const $providerForm = providers.locateProviderForm("oauth2");

        const providerName = formatProviderName("Complete OAuth2");

        const nameField = $providerForm.getByRole("textbox", {
            name: "name",
        });

        await expect(nameField).toBeVisible();

        await nameField.fill(providerName);

        await form.selectAuthorizationFlow(
            $providerForm,
            /default-provider-authorization-explicit-consent/,
        );

        // await form.toggle(
        //     $providerForm,
        //     /default-provider-authorization-explicit-consent/,
        // );

        await wizard.navigation.next.click();
        //     [toggleFormGroup, /Protocol settings/, true],
        //     [setRadio, "clientType", "Public"],
        //     // Switch back so we can make sure `clientSecret` is available.
        //     [setRadio, "clientType", "Confidential"],
        //     [assertVisible, '[name="clientId"]'],
        //     [assertVisible, '[name="clientSecret"]'],
        //     [setSearchSelect, "signingKey", /authentik Self-signed Certificate/],
        //     [setSearchSelect, "encryptionKey", /authentik Self-signed Certificate/],
        //     [toggleFormGroup, /Advanced flow settings/, true],
        //     [setSearchSelect, "authenticationFlow", /default-source-authentication/],
        //     [setSearchSelect, "invalidationFlow", /default-invalidation-flow/],
        //     [toggleFormGroup, /Advanced protocol settings/, true],
        //     [setTextInput, "accessCodeValidity", "minutes=2"],
        //     [setTextInput, "accessTokenValidity", "minutes=10"],
        //     [setTextInput, "refreshTokenValidity", "days=40"],
        //     [setToggle, "includeClaimsInIdToken", false],
        //     [assertVisible, '[name="redirectUris"]'],
        //     [setRadio, "subMode", "Based on the User's username"],
        //     [setRadio, "issuerMode", "Same identifier is used for all providers"],
        //     [toggleFormGroup, /Machine-to-Machine authentication settings/, true],
        //     [assertVisible, '[name="jwtFederationSources"]'],
        //     [assertVisible, '[name="jwtFederationProviders"]'],
        // ];
    });
});
