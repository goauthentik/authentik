import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";
import { aki } from "#common/api/client";

import { AKFlowSearch } from "#admin/common/ak-flow-search/AKFlowSearch";
import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { AuthenticatorStaticStage, FlowDesignationEnum, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-stage-authenticator-static-form")
export class AuthenticatorStaticStageForm extends BaseStageForm<AuthenticatorStaticStage> {
    protected endpoints = {
        load: (stageUuid: string) =>
            aki(StagesApi).stagesAuthenticatorStaticRetrieve({ stageUuid }),
        create: (authenticatorStaticStageRequest: AuthenticatorStaticStage) =>
            aki(StagesApi).stagesAuthenticatorStaticCreate({ authenticatorStaticStageRequest }),
        update: (stageUuid: string, authenticatorStaticStageRequest: AuthenticatorStaticStage) =>
            aki(StagesApi).stagesAuthenticatorStaticUpdate({
                stageUuid,
                authenticatorStaticStageRequest,
            }),
    };

    protected override renderForm(): TemplateResult {
        return html` <span>
                ${msg(
                    "Stage used to configure a static authenticator (i.e. static tokens). This stage should be used for configuration flows.",
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
                    <ak-form-element-horizontal
                        label=${msg("Token count")}
                        required
                        name="tokenCount"
                    >
                        <input
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
                    <ak-form-element-horizontal
                        label=${msg("Token length")}
                        required
                        name="tokenLength"
                    >
                        <input
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
                    <ak-form-element-horizontal
                        label=${msg("Configuration flow")}
                        name="configureFlow"
                    >
                        ${AKFlowSearch({
                            name: "configureFlow",
                            flowType: FlowDesignationEnum.StageConfiguration,
                            value: this.instance?.configureFlow,
                            blankable: true,
                        })}
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
