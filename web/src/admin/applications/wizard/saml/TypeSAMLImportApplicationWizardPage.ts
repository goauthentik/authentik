import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { KeyUnknown } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { WizardFormPage } from "@goauthentik/elements/wizard/WizardFormPage";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { TemplateResult, html } from "lit";

import {
    FlowDesignationEnum,
    FlowsApi,
    ProvidersApi,
    ProvidersSamlImportMetadataCreateRequest,
} from "@goauthentik/api";

@customElement("ak-application-wizard-type-saml-import")
export class TypeSAMLImportApplicationWizardPage extends WizardFormPage {
    sidebarLabel = () => msg("Import SAML metadata");

    nextDataCallback = async (data: KeyUnknown): Promise<boolean> => {
        let name = this.host.state["name"] as string;
        // Check if a provider with the name already exists
        const providers = await new ProvidersApi(DEFAULT_CONFIG).providersAllList({
            search: name,
        });
        if (providers.results.filter((provider) => provider.name == name)) {
            name += "-1";
        }
        this.host.addActionBefore(msg("Create provider"), async (): Promise<boolean> => {
            // Get all flows and default to the implicit authorization
            const flows = await new FlowsApi(DEFAULT_CONFIG).flowsInstancesList({
                designation: FlowDesignationEnum.Authorization,
                ordering: "slug",
            });
            const req: ProvidersSamlImportMetadataCreateRequest = {
                name: name,
                authorizationFlow: flows.results[0].slug,
                file: data["metadata"] as Blob,
            };
            const provider = await new ProvidersApi(
                DEFAULT_CONFIG,
            ).providersSamlImportMetadataCreate(req);
            this.host.state["provider"] = provider;
            return true;
        });
        return true;
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${msg("Metadata")} name="metadata">
                <input type="file" value="" class="pf-c-form-control" />
            </ak-form-element-horizontal>
        </form> `;
    }
}
