import { expect, test } from "#e2e";
import { ProvidersFixture } from "#e2e/fixtures/ProvidersFixture";
import { IDGenerator } from "@goauthentik/core/id";

function formatProviderName(providerName = "Test Provider") {
    return `${providerName} (${IDGenerator.randomID()})`;
}

test.describe("Configure OAuth2 Providers", () => {
    test.beforeEach(async ({ page, session, providers, landmarks, wizard }) => {
        await session.login({
            to: ProvidersFixture.pathname,
        });

        await expect(wizard.$heading, "Wizard is hidden by default").toBeHidden();

        await providers.$newProviderButton.click();

        await wizard.assertVisible();

        await expect(page.locator("ak-wizard-page-type-create")).toBeVisible();

        await expect(wizard.$navigationNext).toBeDisabled();

        const $ouidComponent = landmarks.findOUIDComponent("oauth2provider");

        await $ouidComponent.click();

        await expect(wizard.$navigationNext).toBeEnabled();

        await wizard.nextStep();
    });

    test("Should configure a simple OAuth2 Application", async ({ providers, form, wizard }) => {
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

        await wizard.nextStep();
    });
});
