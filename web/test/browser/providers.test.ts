import { expect, test } from "#e2e";
import { createRandomName } from "#e2e/utils/generators";
import { ConsoleLogger } from "#logger/node";
import { IDGenerator } from "@goauthentik/core/id";
import { series } from "@goauthentik/core/promises";

test.describe("Provider Wizard", () => {
    const providerNames = new Map<string, string>();

    //#region Lifecycle

    test.beforeEach("Configure Providers", async ({ page, session }, { testId }) => {
        const seed = IDGenerator.randomID(6);
        const providerName = `${createRandomName({ seed })} (${seed})`;

        providerNames.set(testId, providerName);

        const wizard = page.getByRole("dialog", { name: "New provider" });

        await test.step("Authenticate", async () => {
            await session.login({
                to: "/if/admin/#/core/providers",
            });
        });

        await test.step("Navigate to provider wizard", async () => {
            await expect(wizard, "Wizard is initially closed").toBeHidden();

            await page.getByRole("button", { name: "New Provider" }).click();

            await expect(wizard, "Wizard opens after clicking on New Provider").toBeVisible();

            await expect(
                page.getByRole("listbox", { name: "Select a provider type" }),
                "Wizard opens with a list of provider types",
            ).toBeVisible();

            await expect(
                wizard.getByRole("navigation").getByRole("button", {
                    name: /next|finish/i,
                }),
                "Wizard can't be navigated to next step",
            ).toBeDisabled();
        });
    });

    test.afterEach("Verification", async ({ page }, { testId }) => {
        //#region Confirm provider

        const providerName = providerNames.get(testId)!;

        const $provider = await test.step("Find provider via search", async () => {
            const searchInput = page.getByRole("search").getByPlaceholder("Search for providers");

            await searchInput.fill(providerName);

            // We have to wait for the provider to appear in the table,
            // but several UI elements will be rendered asynchronously.
            // We attempt several times to find the provider to avoid flakiness.

            const tries = 10;
            let found = false;

            for (let i = 0; i < tries; i++) {
                await searchInput.press("Enter");
                await searchInput.blur();

                const $rowEntry = page.getByRole("row", {
                    name: providerName,
                });

                ConsoleLogger.info(
                    `${i + 1}/${tries} Waiting for provider ${providerName} to appear in the table`,
                );

                found = await $rowEntry
                    .waitFor({
                        timeout: 1500,
                    })
                    .then(() => true)
                    .catch(() => false);

                if (found) {
                    ConsoleLogger.info(`Provider ${providerName} found in the table`);
                    return $rowEntry;
                }
            }

            throw new Error(`Provider ${providerName} not found in the table`);
        });

        await expect($provider, "Provider is visible").toBeVisible();

        //#endregion
    });

    //#endregion

    //#region OAuth2

    test("Simple OAuth2 Provider", async ({ form, pointer }, testInfo) => {
        const providerName = providerNames.get(testInfo.testId)!;
        const { fill, selectSearchValue } = form;
        const { click } = pointer;

        await series(
            [click, "OAuth2/OpenID", "option"],
            [click, "Next"],
            [fill, "Provider name", providerName],
            [
                selectSearchValue,
                "Authorization flow",
                /default-provider-authorization-explicit-consent/,
            ],
            [click, "Finish"],
        );
    });

    test("Complete OAuth2 Provider", async ({ page, form, pointer }, testInfo) => {
        const providerName = providerNames.get(testInfo.testId)!;

        const { fill, selectSearchValue, setFormGroup, setRadio, setInputCheck } = form;
        const { click } = pointer;

        const $clientSecretInput = page.getByRole("textbox", { name: "Client Secret" });

        await series(
            [click, "OAuth2/OpenID", "option"],
            [click, "Next"],
            [fill, "Provider name", providerName],
            [
                selectSearchValue,
                "Authorization flow",
                /default-provider-authorization-explicit-consent/,
            ],
            [setFormGroup, "Protocol settings", true],
            [setRadio, "Client Type", "Public"],
            [
                expect(
                    $clientSecretInput,
                    "Client Secret should be hidden when Client Type is Public",
                ).toBeHidden,
            ],
            [setRadio, "Client Type", "Confidential"],
            [
                expect(
                    $clientSecretInput,
                    "Client Secret should be visible when Client Type is Confidential",
                ).toBeVisible,
            ],
            [selectSearchValue, "Signing Key", /authentik Self-signed Certificate/],
            [selectSearchValue, "Encryption Key", /authentik Self-signed Certificate/],
            [setFormGroup, "Advanced flow settings", true],
            [selectSearchValue, "Authentication flow", /default-source-authentication/],
            [selectSearchValue, "Invalidation flow", /default-invalidation-flow/],
            [setFormGroup, "Advanced protocol settings", true],
            [fill, "Access code validity", "minutes=2"],
            [fill, "Access token validity", "minutes=10"],
            [fill, "Refresh token validity", "days=40"],
            [setInputCheck, "Include claims in id_token", false],
            [setRadio, "Subject mode", "Based on the User's username"],
            [setRadio, "Issuer mode", "Same identifier is used for all providers"],
            [setFormGroup, "Machine-to-Machine authentication settings", true],
            [click, "Finish", "button", page.getByRole("dialog", { name: "New Provider" })],
        );
    });

    //#endregion

    //#region LDAP

    test("Complete LDAP Provider", async ({ page, pointer, form }, testInfo) => {
        const providerName = providerNames.get(testInfo.testId)!;
        const { fill, setFormGroup, selectSearchValue, setInputCheck, setRadio } = form;
        const { click } = pointer;

        await series(
            [click, "LDAP", "option"],
            [click, "Next"],

            [fill, "Provider name", providerName],
            [setFormGroup, "Flow settings", true],
            [setFormGroup, "Protocol settings", true],
            [selectSearchValue, "Bind flow", /default-authentication-flow/],
            [fill, "Base DN", "DC=ldap-2,DC=goauthentik,DC=io"],
            [selectSearchValue, "Certificate", /authentik Self-signed Certificate/],
            [fill, "TLS Server name", "goauthentik.io"],
            [fill, "UID start number", "2001"],
            [fill, "GID start number", "4001"],
            [setRadio, "Search mode", "Direct querying"],
            [setRadio, "Bind mode", "Direct binding"],
            [setInputCheck, "MFA Support", false],
            [click, "Finish", "button", page.getByRole("dialog", { name: "New Provider" })],
        );
    });

    //#endregion

    //#region RADIUS

    test("Complete RADIUS Provider", async ({ page, pointer, form }, testInfo) => {
        const providerName = providerNames.get(testInfo.testId)!;
        const { fill, selectSearchValue } = form;
        const { click } = pointer;

        await series(
            [click, "RADIUS", "option"],
            [click, "Next"],
            [fill, "Provider name", providerName],
            [selectSearchValue, "Authentication flow", /default-authentication-flow/],
            [click, "Finish", "button", page.getByRole("dialog", { name: "New Provider" })],
        );
    });

    //#endregion
});
