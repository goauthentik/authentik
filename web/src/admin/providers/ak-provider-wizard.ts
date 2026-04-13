import "#elements/LicenseNotice";
import "#admin/providers/ldap/LDAPProviderForm";
import "#admin/providers/oauth2/OAuth2ProviderForm";
import "#admin/providers/proxy/ProxyProviderForm";
import "#admin/providers/saml/SAMLProviderForm";
import "#admin/providers/saml/SAMLProviderImportForm";
import "#elements/wizard/FormWizardPage";
import "#elements/wizard/TypeCreateWizardPage";
import "#elements/wizard/Wizard";

import { DEFAULT_CONFIG } from "#common/api/config";

import { CreateWizard } from "#elements/wizard/CreateWizard";
import { TypeCreateWizardPageLayouts } from "#elements/wizard/TypeCreateWizardPage";

import { ProvidersApi, TypeCreate } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";

@customElement("ak-provider-wizard")
export class AKProviderWizard extends CreateWizard {
    #api = new ProvidersApi(DEFAULT_CONFIG);

    public static override verboseName = msg("Provider");
    public static override verboseNamePlural = msg("Providers");

    public override layout = TypeCreateWizardPageLayouts.grid;

    protected apiEndpoint = async (requestInit?: RequestInit): Promise<TypeCreate[]> => {
        return this.#api.providersAllTypesList(requestInit);
    };
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-wizard": AKProviderWizard;
    }
}
