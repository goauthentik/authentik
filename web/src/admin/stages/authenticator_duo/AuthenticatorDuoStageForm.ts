import { RenderFlowOption } from "@goauthentik/admin/flows/utils";
import { BaseStageForm } from "@goauthentik/admin/stages/BaseStageForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/components/ak-secret-text-input.js";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import {
    AuthenticatorDuoStage,
    AuthenticatorDuoStageRequest,
    Flow,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    FlowsInstancesListRequest,
    StagesApi,
} from "@goauthentik/api";

@customElement("ak-stage-authenticator-duo-form")
export class AuthenticatorDuoStageForm extends BaseStageForm<AuthenticatorDuoStage> {
    loadInstance(pk: string): Promise<AuthenticatorDuoStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorDuoRetrieve({
            stageUuid: pk,
        });
    }

    async send(data: AuthenticatorDuoStage): Promise<AuthenticatorDuoStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorDuoPartialUpdate({
                stageUuid: this.instance.pk || "",
                patchedAuthenticatorDuoStageRequest: data,
            });
        }
        return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorDuoCreate({
            authenticatorDuoStageRequest: data as unknown as AuthenticatorDuoStageRequest,
        });
    }

    renderForm(): TemplateResult {
        return html` <span>
                ${msg(
                    "Stage used to configure a duo-based authenticator. This stage should be used for configuration flows.",
                )}
            </span>
            <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${this.instance?.name ?? ""}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Authenticator type name")}
                ?required=${false}
                name="friendlyName"
            >
                <input
                    type="text"
                    value="${this.instance?.friendlyName ?? ""}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Display name of this authenticator, used by users when they enroll an authenticator.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("API Hostname")} required name="apiHostname">
                <input
                    type="text"
                    value="${this.instance?.apiHostname ?? ""}"
                    class="pf-c-form-control pf-m-monospace"
                    autocomplete="off"
                    spellcheck="false"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group open label="${msg("Duo Auth API")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Integration key")}
                        required
                        name="clientId"
                    >
                        <input
                            type="text"
                            value="${this.instance?.clientId ?? ""}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                    <ak-secret-text-input
                        name="clientSecret"
                        label=${msg("Secret key")}
                        input-hint="code"
                        required
                        ?revealed=${this.instance === undefined}
                    ></ak-secret-text-input>
                </div>
            </ak-form-group>
            <ak-form-group
                label=${msg("Duo Admin API (optional)")}
                description="${msg(
                    `When using a Duo MFA, Access or Beyond plan, an Admin API application can be created. This will allow authentik to import devices automatically.`,
                )}"
            >
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Integration key")}
                        name="adminIntegrationKey"
                    >
                        <input
                            type="text"
                            value="${this.instance?.adminIntegrationKey ?? ""}"
                            class="pf-c-form-control pf-m-monospace"
                            autocomplete="off"
                            spellcheck="false"
                        />
                    </ak-form-element-horizontal>
                    <ak-secret-text-input
                        name="adminSecretKey"
                        label=${msg("Secret key")}
                        input-hint="code"
                        ?revealed=${this.instance === undefined}
                    ></ak-secret-text-input>
                </div>
            </ak-form-group>
            <ak-form-group open label="${msg("Stage-specific settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Configuration flow")}
                        name="configureFlow"
                    >
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
                            blankable
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Flow used by an authenticated user to configure this Stage. If empty, user will not be able to configure this stage.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-duo-form": AuthenticatorDuoStageForm;
    }
}
