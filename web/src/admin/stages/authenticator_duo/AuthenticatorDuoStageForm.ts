import "#components/ak-secret-text-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import { aki } from "#common/api/client";

import { AKLabel } from "#components/ak-label";

import { RenderFlowOption } from "#admin/flows/utils";
import { BaseStageForm } from "#admin/stages/BaseStageForm";

import {
    AuthenticatorDuoStage,
    AuthenticatorDuoStageRequest,
    Flow,
    FlowDesignationEnum,
    FlowsApi,
    FlowsInstancesListRequest,
    StagesApi,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-stage-authenticator-duo-form")
export class AuthenticatorDuoStageForm extends BaseStageForm<AuthenticatorDuoStage> {
    protected endpoints = {
        load: (stageUuid: string) => aki(StagesApi).stagesAuthenticatorDuoRetrieve({ stageUuid }),
        create: (authenticatorDuoStageRequest: AuthenticatorDuoStage) =>
            aki(StagesApi).stagesAuthenticatorDuoCreate({
                authenticatorDuoStageRequest:
                    authenticatorDuoStageRequest as unknown as AuthenticatorDuoStageRequest,
            }),
        update: (stageUuid: string, patchedAuthenticatorDuoStageRequest: AuthenticatorDuoStage) =>
            aki(StagesApi).stagesAuthenticatorDuoPartialUpdate({
                stageUuid,
                patchedAuthenticatorDuoStageRequest,
            }),
    };

    protected override renderForm(): TemplateResult {
        return html` <span>
                ${msg(
                    "Stage used to configure a duo-based authenticator. This stage should be used for configuration flows.",
                )}
            </span>
            <ak-form-element-horizontal required name="name">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "name",
                        required: true,
                    },
                    msg("Name"),
                )}
                <input
                    id="name"
                    type="text"
                    value="${this.instance?.name ?? ""}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal ?required=${false} name="friendlyName">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "friendlyName",
                    },
                    msg("Authenticator type name"),
                )}
                <input
                    id="friendlyName"
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
            <ak-form-element-horizontal required name="apiHostname">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "apiHostname",
                        required: true,
                    },
                    msg("API Hostname"),
                )}
                <input
                    id="apiHostname"
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
                    <ak-form-element-horizontal required name="clientId">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "clientId",
                                required: true,
                            },
                            msg("Integration key"),
                        )}
                        <input
                            id="clientId"
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
                        ?required=${!this.instance}
                        ?revealed=${!this.instance}
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
                    <ak-form-element-horizontal name="adminIntegrationKey">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "adminIntegrationKey",
                            },
                            msg("Integration key"),
                        )}
                        <input
                            id="adminIntegrationKey"
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
                        ?revealed=${!this.instance}
                    ></ak-secret-text-input>
                </div>
            </ak-form-group>
            <ak-form-group open label="${msg("Stage-specific settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal name="configureFlow">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "configureFlow",
                            },
                            msg("Configuration flow"),
                        )}
                        <ak-search-select
                            id="configureFlow"
                            .fetchObjects=${async (query?: string): Promise<Flow[]> => {
                                const args: FlowsInstancesListRequest = {
                                    ordering: "slug",
                                    designation: FlowDesignationEnum.StageConfiguration,
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const flows = await aki(FlowsApi).flowsInstancesList(args);
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
