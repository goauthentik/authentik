import "#elements/LicenseNotice";
import "#admin/providers/google_workspace/GoogleWorkspaceProviderForm";
import "#admin/providers/ldap/LDAPProviderForm";
import "#admin/providers/microsoft_entra/MicrosoftEntraProviderForm";
import "#admin/providers/oauth2/OAuth2ProviderForm";
import "#admin/providers/proxy/ProxyProviderForm";
import "#admin/providers/rac/RACProviderForm";
import "#admin/providers/radius/RadiusProviderForm";
import "#admin/providers/saml/SAMLProviderForm";
import "#admin/providers/saml/SAMLProviderImportForm";
import "#admin/providers/scim/SCIMProviderForm";
import "#admin/providers/ssf/SSFProviderFormPage";
import "#admin/providers/wsfed/WSFederationProviderForm";
import "#elements/wizard/FormWizardPage";
import "#elements/wizard/TypeCreateWizardPage";
import "#elements/wizard/Wizard";
import { aki } from "#common/api/client";

import { formatCreateLabel } from "#elements/dialogs/shared";
import { toAdminInterface } from "#elements/router/core/interfaces";
import { CreateWizard } from "#elements/wizard/CreateWizard";
import { TypeCreateWizardPageLayouts } from "#elements/wizard/TypeCreateWizardPage";

import { AKFullPageWizard } from "#components/ak-wizard/ak-full-page-wizard";

import { ProvidersApi, TypeCreate } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html } from "lit";

@customElement("ak-provider-wizard")
export class AKProviderWizard extends CreateWizard {
    #api = aki(ProvidersApi);

    public static override verboseName = msg("Provider");
    public static override verboseNamePlural = msg("Providers");

    public override layout = TypeCreateWizardPageLayouts.grid;

    protected apiEndpoint = async (requestInit?: RequestInit): Promise<TypeCreate[]> => {
        return this.#api.providersAllTypesList(requestInit);
    };
}

/**
 * The provider wizard as a full page, for the `/core/providers/new` route.
 */
@customElement("ak-provider-wizard-page")
export class AKProviderWizardPage extends AKFullPageWizard {
    public override header = formatCreateLabel(AKProviderWizard);
    public override icon = "pf-icon pf-icon-integration";
    public override returnURL = toAdminInterface("core/providers");

    protected override render() {
        return html`<ak-provider-wizard></ak-provider-wizard>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-wizard": AKProviderWizard;
        "ak-provider-wizard-page": AKProviderWizardPage;
    }
}
