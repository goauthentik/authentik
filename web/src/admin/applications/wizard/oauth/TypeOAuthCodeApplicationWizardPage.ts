import "@goauthentik/admin/common/ak-flow-search/ak-flow-search-no-default";
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
    FlowsInstancesListDesignationEnum,
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
                <ak-flow-search-no-default
                    flowType=${FlowsInstancesListDesignationEnum.Authorization}
                    required
                ></ak-flow-search-no-default>
                <p class="pf-c-form__helper-text">
                    ${msg("Flow used when users access this application.")}
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }
}
