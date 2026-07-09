import "#components/ak-text-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import { aki } from "#common/api/client";

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
    protected endpoints = {
        load: (stageUuid: string) => aki(StagesApi).stagesAuthenticatorTotpRetrieve({ stageUuid }),
        create: (authenticatorTOTPStageRequest: AuthenticatorTOTPStage) =>
            aki(StagesApi).stagesAuthenticatorTotpCreate({ authenticatorTOTPStageRequest }),
        update: (stageUuid: string, authenticatorTOTPStageRequest: AuthenticatorTOTPStage) =>
            aki(StagesApi).stagesAuthenticatorTotpUpdate({
                stageUuid,
                authenticatorTOTPStageRequest,
            }),
    };

    protected override renderForm(): TemplateResult {
        return html` <span>
                ${msg(
                    "Stage used to configure a TOTP authenticator (i.e. Authy/Google Authenticator).",
                )}
            </span>
            <ak-text-input
                label=${msg("Stage Name", {
                    id: "stage.name.label",
                })}
                required
                name="name"
                value=${this.instance?.name || ""}
                placeholder=${msg("Type a name for this stage...", {
                    id: "stage.name.placeholder",
                })}
                ?autofocus=${!this.instance}
            ></ak-text-input>
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
            <ak-form-group open label="${msg("Stage-specific settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("Digits")} required name="digits">
                        <select name="users" class="pf-c-form-control">
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
                    <ak-form-element-horizontal
                        label=${msg("Configuration flow")}
                        name="configureFlow"
                    >
                        <ak-search-select
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
        "ak-stage-authenticator-totp-form": AuthenticatorTOTPStageForm;
    }
}
