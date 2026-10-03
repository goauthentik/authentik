import "#admin/sources/kerberos/KerberosSourceForm";
import "#admin/sources/ldap/LDAPSourceForm";
import "#admin/sources/oauth/OAuthSourceForm";
import "#admin/sources/plex/PlexSourceForm";
import "#admin/sources/saml/SAMLSourceForm";
import "#admin/sources/scim/SCIMSourceForm";
import "#admin/sources/telegram/TelegramSourceForm";
import "#elements/wizard/FormWizardPage";
import "#elements/wizard/Wizard";
import { aki } from "#common/api/client";

import { formatCreateLabel } from "#elements/dialogs/shared";
import { toAdminInterface } from "#elements/router/core/interfaces";
import { LitPropertyRecord } from "#elements/types";
import { CreateWizard } from "#elements/wizard/CreateWizard";
import { TypeCreateWizardPageLayouts } from "#elements/wizard/TypeCreateWizardPage";

import { AKFullPageWizard } from "#components/ak-wizard/ak-full-page-wizard";

import { BaseSourceForm } from "#admin/sources/BaseSourceForm";

import { SourcesApi, TypeCreate } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html } from "lit";

@customElement("ak-source-wizard")
export class AKSourceWizard extends CreateWizard {
    #api = aki(SourcesApi);

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

/**
 * The source wizard as a full page, for the `/core/sources/new` route.
 */
@customElement("ak-source-wizard-page")
export class AKSourceWizardPage extends AKFullPageWizard {
    public override header = formatCreateLabel(AKSourceWizard);
    public override icon = "pf-icon pf-icon-middleware";
    public override returnURL = toAdminInterface("core/sources");

    protected override render() {
        return html`<ak-source-wizard></ak-source-wizard>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-wizard": AKSourceWizard;
        "ak-source-wizard-page": AKSourceWizardPage;
    }
}
