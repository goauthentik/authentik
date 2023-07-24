import "@goauthentik/admin/common/ak-flow-search/ak-flow-search-no-default";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { SentryIgnoredError } from "@goauthentik/common/errors";
import { Form } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import { FlowsInstancesListDesignationEnum, ProvidersApi, SAMLProvider } from "@goauthentik/api";

@customElement("ak-provider-saml-import-form")
export class SAMLProviderImportForm extends Form<SAMLProvider> {
    getSuccessMessage(): string {
        return msg("Successfully imported provider.");
    }

    async send(data: SAMLProvider): Promise<void> {
        const file = this.getFormFiles()["metadata"];
        if (!file) {
            throw new SentryIgnoredError("No form data");
        }
        return new ProvidersApi(DEFAULT_CONFIG).providersSamlImportMetadataCreate({
            file: file,
            name: data.name,
            authorizationFlow: data.authorizationFlow || "",
        });
    }

    renderInlineForm(): TemplateResult {
        return html`<ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input type="text" class="pf-c-form-control" required />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Authorization flow")}
                ?required=${true}
                name="authorizationFlow"
            >
                <ak-flow-search-no-default
                    flowType=${FlowsInstancesListDesignationEnum.Authorization}
                    required
                ></ak-flow-search-no-default>
                <p class="pf-c-form__helper-text">
                    ${msg("Flow used when authorizing this provider.")}
                </p>
            </ak-form-element-horizontal>

            <ak-form-element-horizontal label=${msg("Metadata")} name="metadata">
                <input type="file" value="" class="pf-c-form-control" />
            </ak-form-element-horizontal>`;
    }
}
