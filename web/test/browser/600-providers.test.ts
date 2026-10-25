import { expect, test } from "#e2e";
import { randomName } from "#e2e/utils/generators";

import { IDGenerator } from "@goauthentik/core/id";
import { series } from "@goauthentik/core/promises";

test.describe("Provider Wizard", () => {
    const providerNames = new Map<string, string>();

    //#region Lifecycle

    test.beforeEach("Configure Providers", async ({ page, session }, { testId }) => {
        const seed = IDGenerator.randomID(6);
        const providerName = `${randomName(seed)} (${seed})`;

        providerNames.set(testId, providerName);

        const dialog = page.getByRole("dialog", { name: "New Provider Wizard" });

        await test.step("Authenticate", async () =>
            session.login({
                to: "/if/admin/core/providers",
            }));

        await test.step("Navigate to provider wizard", async () => {
            await expect(dialog, "Dialog is initially closed").toBeHidden();

            // Scoped to the toolbar: `Table` renders the create control twice —
            // once here and once inside the empty state it shows while the rows
            // are still loading (`renderEmpty`). An unscoped locator matches both
            // and fails strict mode, which is timing-dependent and so only bites
            // when the request is slow.
            await page
                .locator('[part="toolbar-secondary"]')
                .getByRole("button", { name: "New Provider" })
                .click();

            await expect(dialog, "Dialog opens after clicking on New Provider").toBeVisible();

            await expect(
                page.getByRole("listbox", { name: "Choose Provider Type" }),
                "Dialog opens with a list of provider types",
            ).toBeVisible();

            await expect(
                dialog.getByRole("navigation").getByRole("button", {
                    name: /next|finish/i,
                }),
                "Dialog can't be navigated to next step",
            ).toBeDisabled();
        });
    });

    test.afterEach("Verification", async ({ form }, { testId }) => {
        //#region Confirm provider

        const providerName = providerNames.get(testId)!;
        const { search } = form;

        const $provider = await test.step("Find provider via search", () => search(providerName));

        await expect($provider, "Provider is visible").toBeVisible();

        //#endregion
    });

    //#endregion

    //#region OAuth2

    test("Simple OAuth2 Provider", async ({ form, pointer, page }, testInfo) => {
        const providerName = providerNames.get(testInfo.testId)!;
        const { fill, selectSearchValue } = form;
        const { click } = pointer;
        const dialog = page.getByRole("dialog", { name: "New Provider Wizard" });

        await series(
            [click, "OAuth2/OpenID", "option"],
            [fill, "Provider Name", providerName],
            [
                selectSearchValue,
                "Authorization Flow",
                /default-provider-authorization-explicit-consent/,
            ],
            [click, "Create", "button", dialog],
        );
    });

    test("OAuth2 Provider submitted while a default flow is still loading", async ({
        form,
        pointer,
        page,
    }, testInfo) => {
        const providerName = providerNames.get(testInfo.testId)!;
        const { fill, selectSearchValue } = form;
        const { click } = pointer;
        const dialog = page.getByRole("dialog", { name: "New Provider Wizard" });

        await test.step("Slow down loading the invalidation flows", async () => {
            await page.route(/\/flows\/instances\/.*designation=invalidation/, async (route) => {
                await new Promise((resolve) => setTimeout(resolve, 3_000));
                await route.continue();
            });
        });

        const request = page.waitForRequest(
            (request) =>
                request.method() === "POST" && request.url().includes("/providers/oauth2/"),
        );

        await test.step("Create the provider without waiting for the defaults", async () => {
            await series(
                [click, "OAuth2/OpenID", "option"],
                [fill, "Provider Name", providerName],
                [
                    selectSearchValue,
                    "Authorization Flow",
                    /default-provider-authorization-explicit-consent/,
                ],
                [click, "Create", "button", dialog],
            );
        });

        await test.step("The default invalidation flow is submitted", async () => {
            const { invalidation_flow } = (await request).postDataJSON();

            expect(invalidation_flow, "Invalidation flow is not null").toEqual(expect.any(String));

            await expect(dialog, "Dialog closes after creation").toBeHidden();
        });
    });

    test("OAuth2 Provider chosen with the keyboard and search", async ({
        form,
        pointer,
        page,
    }, testInfo) => {
        const providerName = providerNames.get(testInfo.testId)!;
        const { fill, findSearchSelect } = form;
        const { click } = pointer;
        const dialog = page.getByRole("dialog", { name: "New Provider Wizard" });

        await click("OAuth2/OpenID", "option");
        await fill("Provider Name", providerName, dialog);

        const { host, combobox } = await findSearchSelect("Authorization Flow", dialog);
        const listbox = host.getByRole("listbox");

        await test.step("Open with the keyboard and search", async () => {
            await combobox.focus();
            await combobox.press("ArrowDown");

            await expect(listbox, "ArrowDown opens the options").toBeVisible();

            await combobox.fill("implicit");

            await expect(host.getByRole("option"), "Only the matching flow is listed").toHaveCount(
                1,
            );
        });

        await test.step("Choose with the keyboard", async () => {
            await combobox.press("ArrowDown");
            await combobox.press("Enter");

            await expect(listbox, "Choosing closes the options").toBeHidden();

            await expect(combobox, "The chosen flow's label is shown").toHaveValue(
                /default-provider-authorization-implicit-consent/,
            );
        });

        await test.step("Close by clicking outside", async () => {
            await combobox.click();

            await expect(listbox, "Clicking the field opens the options").toBeVisible();

            await dialog.getByRole("heading", { name: "Create New Provider" }).click();

            await expect(listbox, "Clicking outside closes the options").toBeHidden();
        });

        await click("Create", "button", dialog);
    });

    test("Saved OAuth2 Provider shows its flows and signing key", async ({
        form,
        pointer,
        page,
    }, testInfo) => {
        const providerName = providerNames.get(testInfo.testId)!;
        const { fill, search, findSearchSelect, selectSearchValue, setFormGroup } = form;
        const { click } = pointer;
        const wizard = page.getByRole("dialog", { name: "New Provider Wizard" });

        await test.step("Create the provider", async () => {
            await series(
                [click, "OAuth2/OpenID", "option"],
                [fill, "Provider Name", providerName],
                [
                    selectSearchValue,
                    "Authorization Flow",
                    /default-provider-authorization-explicit-consent/,
                ],
                [click, "Create", "button", wizard],
            );

            await expect(wizard, "Wizard closes after creation").toBeHidden();
        });

        const editDialog = page.getByRole("dialog");

        await test.step("Open the provider's edit form", async () => {
            const $provider = await search(providerName);

            await $provider.getByRole("button", { name: /Edit/ }).first().click();

            await expect(editDialog, "Edit form opens").toBeVisible();
        });

        await test.step("The saved choices are shown by label", async () => {
            const authorization = await findSearchSelect("Authorization Flow", editDialog);

            await expect(authorization.combobox, "Authorization flow is labeled").toHaveValue(
                /default-provider-authorization-explicit-consent/,
            );

            const signingKey = await findSearchSelect("Signing Key", editDialog);

            await expect(signingKey.combobox, "Signing key is labeled").toHaveValue(
                "authentik Self-signed Certificate",
            );

            await setFormGroup(/Advanced flow settings/, true, editDialog);

            const invalidation = await findSearchSelect("Invalidation Flow", editDialog);

            await expect(invalidation.combobox, "Invalidation flow is labeled").toHaveValue(
                /default-provider-invalidation-flow/,
            );
        });
    });

    test("Complete OAuth2 Provider", async ({ page, form, pointer }, testInfo) => {
        const providerName = providerNames.get(testInfo.testId)!;

        const { fill, selectSearchValue, setFormGroup, setRadio, setInputCheck } = form;
        const { click } = pointer;
        const dialog = page.getByRole("dialog", { name: "New Provider Wizard" });

        const $clientSecretInput = page.getByRole("textbox", { name: "Client Secret" });

        await series(
            [click, "OAuth2/OpenID", "option"],
            [fill, "Provider Name", providerName],
            [
                selectSearchValue,
                "Authorization Flow",
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
            [setFormGroup, "Advanced flow settings", true],
            [selectSearchValue, "Authentication Flow", /default-source-authentication/],
            [selectSearchValue, "Invalidation Flow", /default-invalidation-flow/],
            [setFormGroup, "Advanced protocol settings", true],
            [fill, "Access Code Validity", "minutes=2"],
            [fill, "Access Token Validity", "minutes=10"],
            [fill, "Refresh Token Validity", "days=40"],
            [selectSearchValue, "Encryption Key", /authentik Self-signed Certificate/],
            [setInputCheck, "Include claims in id_token", false],
            [setRadio, "Subject Mode", "Based on the User's username"],
            [setRadio, "Issuer Mode", "Same identifier is used for all providers"],
            [setFormGroup, "Machine-to-Machine authentication settings", true],
            [click, "Create", "button", dialog],
        );
    });

    //#endregion

    //#region LDAP

    test("Complete LDAP Provider", async ({ page, pointer, form }, testInfo) => {
        const providerName = providerNames.get(testInfo.testId)!;
        const { fill, setFormGroup, selectSearchValue, setInputCheck, setRadio } = form;
        const { click } = pointer;
        const dialog = page.getByRole("dialog", { name: "New Provider Wizard" });

        await series(
            [click, "LDAP", "option"],
            [fill, "Provider Name", providerName],
            [setFormGroup, "Flow settings", true],
            [setFormGroup, "Protocol settings", true],
            [selectSearchValue, "Bind Flow", /default-authentication-flow/],
            [fill, "Base DN", "DC=ldap-2,DC=goauthentik,DC=io"],
            [selectSearchValue, "Certificate", /authentik Self-signed Certificate/],
            [fill, "TLS Server Name", "goauthentik.io"],
            [fill, "UID Start Number", "2001"],
            [fill, "GID Start Number", "4001"],
            [setRadio, "Search Mode", "Direct querying"],
            [setRadio, "Bind Mode", "Direct binding"],
            [setInputCheck, "MFA Support", false],
            [click, "Create", "button", dialog],
        );
    });

    //#endregion

    //#region RADIUS

    test("Complete RADIUS Provider", async ({ page, pointer, form }, testInfo) => {
        const providerName = providerNames.get(testInfo.testId)!;
        const { fill, selectSearchValue, setFormGroup } = form;
        const { click } = pointer;
        const dialog = page.getByRole("dialog", { name: "New Provider Wizard" });

        await series(
            [click, "RADIUS", "option"],
            [fill, "Provider Name", providerName],
            [selectSearchValue, "Authentication Flow", /default-authentication-flow/],
            [setFormGroup, "Protocol settings", true],
            [selectSearchValue, "Certificate", /------/],
            [click, "Create", "button", dialog],
        );
    });

    //#endregion
});
