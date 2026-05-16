import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKLabel } from "#components/ak-label";

import { RenderFlowOption } from "#admin/flows/utils";
import { BaseStageForm } from "#admin/stages/BaseStageForm";

import {
    AuthenticatorTOTPStage,
    DigitsEnum,
    Flow,
    FlowDesignationEnum,
    FlowsApi,
    FlowsInstancesListRequest,
    StagesApi,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-stage-authenticator-totp-form")
export class AuthenticatorTOTPStageForm extends BaseStageForm<AuthenticatorTOTPStage> {
    loadInstance(pk: string): Promise<AuthenticatorTOTPStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorTotpRetrieve({
            stageUuid: pk,
        });
    }

    async send(data: AuthenticatorTOTPStage): Promise<AuthenticatorTOTPStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorTotpUpdate({
                stageUuid: this.instance.pk || "",
                authenticatorTOTPStageRequest: data,
            });
        }
        return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorTotpCreate({
            authenticatorTOTPStageRequest: data,
        });
    }

    protected override renderForm(): TemplateResult {
        return html` <span>
                ${msg(
                    "Stage used to configure a TOTP authenticator (i.e. Authy/Google Authenticator).",
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
                    <ak-form-element-horizontal required name="digits">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "digits",
                                required: true,
                            },
                            msg("Digits"),
                        )}
                        <select id="digits" name="users" class="pf-c-form-control">
                            <option
                                value="${DigitsEnum._6}"
                                ?selected=${this.instance?.digits === DigitsEnum._6}
                            >
                                ${msg("6 digits, widely compatible")}
                            </option>
                            <option
                                value="${DigitsEnum._8}"
                                ?selected=${this.instance?.digits === DigitsEnum._8}
                            >
                                ${msg(
                                    "8 digits, not compatible with apps like Google Authenticator",
                                )}
                            </option>
                        </select>
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
        "ak-stage-authenticator-totp-form": AuthenticatorTOTPStageForm;
    }
}
