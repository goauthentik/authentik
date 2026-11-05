import "#admin/sources/kerberos/KerberosSourceForm";
import "#admin/sources/ldap/LDAPSourceForm";
import "#admin/sources/oauth/OAuthSourceForm";
import "#admin/sources/plex/PlexSourceForm";
import "#admin/sources/saml/SAMLSourceForm";
import "#admin/sources/scim/SCIMSourceForm";
import "#admin/sources/telegram/TelegramSourceForm";
import "#admin/sources/SourceLoginStagesWizardPage";
import "#elements/wizard/FormWizardPage";
import "#elements/wizard/Wizard";
import { aki } from "#common/api/client";

import { LitPropertyRecord, SlottedTemplateResult } from "#elements/types";
import { CreateWizard } from "#elements/wizard/CreateWizard";
import { TypeCreateWizardPageLayouts } from "#elements/wizard/TypeCreateWizardPage";

import { BaseSourceForm } from "#admin/sources/BaseSourceForm";

import { SourcesApi, TypeCreate } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html } from "lit";

// Source types that render a button on the login page.
const loginButtonSourceModels = [
    "oauthsource",
    "samlsource",
    "plexsource",
    "telegramsource",
    "kerberossource",
];

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

    protected override selectSteps(type: TypeCreate, currentSteps: string[]): string[] {
        const steps = super.selectSteps(type, currentSteps);

        if (!loginButtonSourceModels.some((model) => type.modelName.includes(model))) {
            return steps;
        }

        return [...steps, "login-stages"];
    }

    protected override renderForms(): SlottedTemplateResult {
        return [
            super.renderForms(),
            html`<ak-source-wizard-page-login-stages
                slot="login-stages"
                headline=${msg("Show on login page", {
                    id: "source.wizard.login-stages.label",
                })}
            ></ak-source-wizard-page-login-stages>`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-wizard": AKSourceWizard;
    }
}
