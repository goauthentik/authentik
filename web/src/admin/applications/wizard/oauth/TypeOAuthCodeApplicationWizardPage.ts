import { RenderFlowOption } from "@goauthentik/admin/flows/utils";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { KeyUnknown } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/SearchSelect";
import { WizardFormPage } from "@goauthentik/elements/wizard/WizardFormPage";
import "@goauthentik/elements/wizard/WizardFormPage";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { TemplateResult, html } from "lit";

import {
    ClientTypeEnum,
    Flow,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    FlowsInstancesListRequest,
    OAuth2ProviderRequest,
    ProvidersApi,
} from "@goauthentik/api";

@customElement("ak-application-wizard-type-oauth-code")
export class TypeOAuthCodeApplicationWizardPage extends WizardFormPage {
    sidebarLabel = () => msg("Method details");

    nextDataCallback = async (data: KeyUnknown): Promise<boolean> => {
        this.host.addActionBefore(msg("Create provider"), async (): Promise<boolean> => {
            const req: OAuth2ProviderRequest = {
                name: this.host.state["name"] as string,
                clientType: ClientTypeEnum.Confidential,
                authorizationFlow: data.authorizationFlow as string,
            };
            const provider = await new ProvidersApi(DEFAULT_CONFIG).providersOauth2Create({
                oAuth2ProviderRequest: req,
            });
            this.host.state["provider"] = provider;
            return true;
        });
        return true;
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${msg("Authorization flow")}
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
                        return flow?.pk;
                    }}
                >
                </ak-search-select>
                <p class="pf-c-form__helper-text">
                    ${msg("Flow used when users access this application.")}
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }
}
