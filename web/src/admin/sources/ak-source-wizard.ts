import "#admin/sources/kerberos/KerberosSourceForm";
import "#admin/sources/ldap/LDAPSourceForm";
import "#admin/sources/oauth/OAuthSourceForm";
import "#admin/sources/plex/PlexSourceForm";
import "#admin/sources/saml/SAMLSourceForm";
import "#admin/sources/scim/SCIMSourceForm";
import "#admin/sources/telegram/TelegramSourceForm";
import "#elements/wizard/FormWizardPage";
import "#elements/wizard/Wizard";

import { DEFAULT_CONFIG } from "#common/api/config";

import { LitPropertyRecord } from "#elements/types";
import { CreateWizard } from "#elements/wizard/CreateWizard";
import { TypeCreateWizardPageLayouts } from "#elements/wizard/TypeCreateWizardPage";

import { BaseSourceForm } from "#admin/sources/BaseSourceForm";

import { SourcesApi, TypeCreate } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";

@customElement("ak-source-wizard")
export class AKSourceWizard extends CreateWizard {
    #api = new SourcesApi(DEFAULT_CONFIG);

    public static override verboseName = msg("Source");
    public static override verboseNamePlural = msg("Sources");

    public override layout = TypeCreateWizardPageLayouts.grid;

    protected apiEndpoint = async (requestInit?: RequestInit): Promise<TypeCreate[]> => {
        return this.#api.sourcesAllTypesList(requestInit);
    };

    protected override assembleFormProps(
        type: TypeCreate,
    ): LitPropertyRecord<BaseSourceForm | object> {
        const props = type.modelName.includes("oauthsource") ? { modelName: type.modelName } : {};

        return props;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-wizard": AKSourceWizard;
    }
}
