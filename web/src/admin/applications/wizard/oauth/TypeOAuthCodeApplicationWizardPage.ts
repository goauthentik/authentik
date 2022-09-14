import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { KeyUnknown } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { WizardFormPage } from "@goauthentik/elements/wizard/WizardFormPage";
import "@goauthentik/elements/wizard/WizardFormPage";

import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { TemplateResult, html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import {
    ClientTypeEnum,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    OAuth2ProviderRequest,
    ProvidersApi,
} from "@goauthentik/api";

@customElement("ak-application-wizard-type-oauth-code")
export class TypeOAuthCodeApplicationWizardPage extends WizardFormPage {
    sidebarLabel = () => t`Method details`;

    nextDataCallback = async (data: KeyUnknown): Promise<boolean> => {
        this.host.addActionBefore(t`Create provider`, async (): Promise<boolean> => {
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
                label=${t`Authorization flow`}
                ?required=${true}
                name="authorizationFlow"
            >
                <select class="pf-c-form-control">
                    ${until(
                        new FlowsApi(DEFAULT_CONFIG)
                            .flowsInstancesList({
                                ordering: "slug",
                                designation: FlowsInstancesListDesignationEnum.Authorization,
                            })
                            .then((flows) => {
                                return flows.results.map((flow) => {
                                    return html`<option value=${ifDefined(flow.pk)}>
                                        ${flow.name} (${flow.slug})
                                    </option>`;
                                });
                            }),
                        html`<option>${t`Loading...`}</option>`,
                    )}
                </select>
                <p class="pf-c-form__helper-text">
                    ${t`Flow used when users access this application.`}
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }
}
