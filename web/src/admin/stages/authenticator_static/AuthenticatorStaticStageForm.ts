import { RenderFlowOption } from "@goauthentik/admin/flows/utils";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/SearchSelect";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import {
    AuthenticatorStaticStage,
    Flow,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    FlowsInstancesListRequest,
    StagesApi,
} from "@goauthentik/api";

@customElement("ak-stage-authenticator-static-form")
export class AuthenticatorStaticStageForm extends ModelForm<AuthenticatorStaticStage, string> {
    loadInstance(pk: string): Promise<AuthenticatorStaticStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorStaticRetrieve({
            stageUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated stage.`;
        } else {
            return t`Successfully created stage.`;
        }
    }

    send = (data: AuthenticatorStaticStage): Promise<AuthenticatorStaticStage> => {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorStaticUpdate({
                stageUuid: this.instance.pk || "",
                authenticatorStaticStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorStaticCreate({
                authenticatorStaticStageRequest: data,
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`Stage used to configure a static authenticator (i.e. static tokens). This stage should be used for configuration flows.`}
            </div>
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${first(this.instance?.name, "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Authenticator type name`}
                ?required=${false}
                name="friendlyName"
            >
                <input
                    type="text"
                    value="${first(this.instance?.friendlyName, "")}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">
                    ${t`Display name of this authenticator, used by users when they enroll an authenticator.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${t`Stage-specific settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Token count`}
                        ?required=${true}
                        name="tokenCount"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.tokenCount, 6)}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`Configuration flow`} name="configureFlow">
                        <ak-search-select
                            .fetchObjects=${async (query?: string): Promise<Flow[]> => {
                                const args: FlowsInstancesListRequest = {
                                    ordering: "slug",
                                    designation:
                                        FlowsInstancesListDesignationEnum.StageConfiguration,
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const flows = await new FlowsApi(DEFAULT_CONFIG).flowsInstancesList(
                                    args,
                                );
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
                            .selected=${(flow: Flow): boolean => {
                                return this.instance?.configureFlow === flow.pk;
                            }}
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${t`Flow used by an authenticated user to configure this Stage. If empty, user will not be able to configure this stage.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
