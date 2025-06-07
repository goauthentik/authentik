import { PageFixture } from "#e2e/fixtures/PageFixture";
import { Page } from "@playwright/test";

export type ProviderFormName =
    | "saml"
    | "oauth2"
    | "proxy"
    | "ldap"
    | "scim"
    | "radius"
    | "rac"
    | "google-workspace"
    | "microsoft-entra"
    | "ssf";

export class ProvidersFixture extends PageFixture {
    static fixtureName = "ProvidersList";
    static pathname = "/if/admin/#/core/providers";

    //#region Selectors

    public readonly $newProviderButton = this.page.getByTestId("new-provider-button");
    public readonly $searchInput = this.page.getByTestId("table-search-input");
    public readonly $searchButton = this.page.getByTestId("table-search-submit");

    //#endregion

    //#region Public Methods

    /**
     * Find a provider form by its type.
     */
    public locateProviderForm(providerFormName: ProviderFormName) {
        return this.page.locator(`ak-provider-${providerFormName}-form`);
    }

    //#endregion

    //#region Lifecycle

    constructor(page: Page, testName: string) {
        super({ page, testName });
    }

    //#endregion

    //#region Navigation

    public toProvidersListPage() {
        return this.page.goto(ProvidersFixture.pathname);
    }

    //#endregion
}
