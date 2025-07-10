import "#admin/common/ak-flow-search/ak-flow-search-no-default";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { SentryIgnoredError } from "#common/sentry/index";

import { Form } from "#elements/forms/Form";

import { FlowsInstancesListDesignationEnum, ProvidersApi, SAMLProvider } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-provider-saml-import-form")
export class SAMLProviderImportForm extends Form<SAMLProvider> {
    getSuccessMessage(): string {
        return msg("Successfully imported provider.");
    }

    async send(data: SAMLProvider): Promise<void> {
        const file = this.files().get("metadata");
        if (!file) {
            throw new SentryIgnoredError("No form data");
        }
        return new ProvidersApi(DEFAULT_CONFIG).providersSamlImportMetadataCreate({
            file: file,
            name: data.name,
            authorizationFlow: data.authorizationFlow || "",
            invalidationFlow: data.invalidationFlow || "",
        });
    }

    renderForm(): TemplateResult {
        return html`<ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input type="text" class="pf-c-form-control" required />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Authorization flow")}
                required
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
            <ak-form-element-horizontal
                label=${msg("Invalidation flow")}
                required
                name="invalidationFlow"
            >
                <ak-flow-search-no-default
                    flowType=${FlowsInstancesListDesignationEnum.Invalidation}
                    defaultFlowSlug="default-provider-invalidation-flow"
                    required
                ></ak-flow-search-no-default>
                <p class="pf-c-form__helper-text">
                    ${msg("Flow used when logging out of this provider.")}
                </p>
            </ak-form-element-horizontal>

            <ak-form-element-horizontal label=${msg("Metadata")} name="metadata">
                <input type="file" value="" class="pf-c-form-control" />
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-saml-import-form": SAMLProviderImportForm;
    }
}
