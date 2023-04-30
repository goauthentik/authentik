import { RenderFlowOption } from "@goauthentik/admin/flows/utils";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { SentryIgnoredError } from "@goauthentik/common/errors";
import { Form } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/SearchSelect";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import {
    Flow,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    FlowsInstancesListRequest,
    ProvidersApi,
    SAMLProvider,
} from "@goauthentik/api";

@customElement("ak-provider-saml-import-form")
export class SAMLProviderImportForm extends Form<SAMLProvider> {
    getSuccessMessage(): string {
        return t`Successfully imported provider.`;
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

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input type="text" class="pf-c-form-control" required />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Authorization flow`}
                ?required=${true}
                name="authorizationFlow"
            >
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<Flow[]> => {
                        const args: FlowsInstancesListRequest = {
                            ordering: "slug",
                            designation: FlowsInstancesListDesignationEnum.Authorization,
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const flows = await new FlowsApi(DEFAULT_CONFIG).flowsInstancesList(args);
                        return flows.results;
                    }}
                    .renderElement=${(flow: Flow): string => {
                        return RenderFlowOption(flow);
                    }}
                    .renderDescription=${(flow: Flow): TemplateResult => {
                        return html`${flow.name}`;
                    }}
                    .value=${(flow: Flow | undefined): string | undefined => {
                        return flow?.slug;
                    }}
                >
                </ak-search-select>
                <p class="pf-c-form__helper-text">
                    ${t`Flow used when authorizing this provider.`}
                </p>
            </ak-form-element-horizontal>

            <ak-form-element-horizontal label=${t`Metadata`} name="metadata">
                <input type="file" value="" class="pf-c-form-control" />
            </ak-form-element-horizontal>
        </form>`;
    }
}
