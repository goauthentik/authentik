import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import { aki } from "#common/api/client";

import { AKLabel } from "#components/ak-label";

import { RenderFlowOption } from "#admin/flows/utils";
import { BaseStageForm } from "#admin/stages/BaseStageForm";

import {
    AuthenticatorStaticStage,
    Flow,
    FlowDesignationEnum,
    FlowsApi,
    FlowsInstancesListRequest,
    StagesApi,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-stage-authenticator-static-form")
export class AuthenticatorStaticStageForm extends BaseStageForm<AuthenticatorStaticStage> {
    loadInstance(pk: string): Promise<AuthenticatorStaticStage> {
        return aki(StagesApi).stagesAuthenticatorStaticRetrieve({
            stageUuid: pk,
        });
    }

    async send(data: AuthenticatorStaticStage): Promise<AuthenticatorStaticStage> {
        if (this.instance) {
            return aki(StagesApi).stagesAuthenticatorStaticUpdate({
                stageUuid: this.instance.pk || "",
                authenticatorStaticStageRequest: data,
            });
        }
        return aki(StagesApi).stagesAuthenticatorStaticCreate({
            authenticatorStaticStageRequest: data,
        });
    }

    protected override renderForm(): TemplateResult {
        return html` <span>
                ${msg(
                    "Stage used to configure a static authenticator (i.e. static tokens). This stage should be used for configuration flows.",
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
            <ak-form-group open label="${msg("Stage-specific settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal required name="tokenCount">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "tokenCount",
                                required: true,
                            },
                            msg("Token count"),
                        )}
                        <input
                            id="tokenCount"
                            type="text"
                            value="${this.instance?.tokenCount ?? 6}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "The number of tokens generated whenever this stage is used. Every token generated per stage execution will be attached to a single static device.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal required name="tokenLength">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "tokenLength",
                                required: true,
                            },
                            msg("Token length"),
                        )}
                        <input
                            id="tokenLength"
                            type="number"
                            value="${this.instance?.tokenLength ?? 12}"
                            min="1"
                            max="100"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "The length of the individual generated tokens. Can be set to a maximum of 100 characters.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
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
        "ak-stage-authenticator-static-form": AuthenticatorStaticStageForm;
    }
}
