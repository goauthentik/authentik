import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/SearchSelect";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    AuthenticateWebAuthnStage,
    AuthenticatorAttachmentEnum,
    Flow,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    FlowsInstancesListRequest,
    ResidentKeyRequirementEnum,
    StagesApi,
    UserVerificationEnum,
} from "@goauthentik/api";

@customElement("ak-stage-authenticator-webauthn-form")
export class AuthenticateWebAuthnStageForm extends ModelForm<AuthenticateWebAuthnStage, string> {
    loadInstance(pk: string): Promise<AuthenticateWebAuthnStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorWebauthnRetrieve({
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

    send = (data: AuthenticateWebAuthnStage): Promise<AuthenticateWebAuthnStage> => {
        if (data.authenticatorAttachment?.toString() === "") {
            data.authenticatorAttachment = null;
        }
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorWebauthnUpdate({
                stageUuid: this.instance.pk || "",
                authenticateWebAuthnStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorWebauthnCreate({
                authenticateWebAuthnStageRequest: data,
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`Stage used to configure a WebAutnn authenticator (i.e. Yubikey, FaceID/Windows Hello).`}
            </div>
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${t`Stage-specific settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`User verification`}
                        ?required=${true}
                        name="userVerification"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value="${UserVerificationEnum.Required}"
                                ?selected=${this.instance?.userVerification ===
                                UserVerificationEnum.Required}
                            >
                                ${t`User verification must occur.`}
                            </option>
                            <option
                                value="${UserVerificationEnum.Preferred}"
                                ?selected=${this.instance?.userVerification ===
                                UserVerificationEnum.Preferred}
                            >
                                ${t`User verification is preferred if available, but not required.`}
                            </option>
                            <option
                                value="${UserVerificationEnum.Discouraged}"
                                ?selected=${this.instance?.userVerification ===
                                UserVerificationEnum.Discouraged}
                            >
                                ${t`User verification should not occur.`}
                            </option>
                        </select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Resident key requirement`}
                        ?required=${true}
                        name="residentKeyRequirement"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value="${ResidentKeyRequirementEnum.Discouraged}"
                                ?selected=${this.instance?.residentKeyRequirement ===
                                ResidentKeyRequirementEnum.Discouraged}
                            >
                                ${t`The authenticator should not create a dedicated credential`}
                            </option>
                            <option
                                value="${ResidentKeyRequirementEnum.Preferred}"
                                ?selected=${this.instance?.residentKeyRequirement ===
                                ResidentKeyRequirementEnum.Preferred}
                            >
                                ${t`The authenticator can create and store a dedicated credential, but if it doesn't that's alright too`}
                            </option>
                            <option
                                value="${ResidentKeyRequirementEnum.Required}"
                                ?selected=${this.instance?.residentKeyRequirement ===
                                ResidentKeyRequirementEnum.Required}
                            >
                                ${t`The authenticator MUST create a dedicated credential. If it cannot, the RP is prepared for an error to occur`}
                            </option>
                        </select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Authenticator Attachment`}
                        ?required=${true}
                        name="authenticatorAttachment"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value=""
                                ?selected=${this.instance?.authenticatorAttachment === null}
                            >
                                ${t`No preference is sent`}
                            </option>
                            <option
                                value="${AuthenticatorAttachmentEnum.Platform}"
                                ?selected=${this.instance?.authenticatorAttachment ===
                                AuthenticatorAttachmentEnum.Platform}
                            >
                                ${t`A non-removable authenticator, like TouchID or Windows Hello`}
                            </option>
                            <option
                                value="${AuthenticatorAttachmentEnum.CrossPlatform}"
                                ?selected=${this.instance?.authenticatorAttachment ===
                                AuthenticatorAttachmentEnum.CrossPlatform}
                            >
                                ${t`A "roaming" authenticator, like a YubiKey`}
                            </option>
                        </select>
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
                                return flow.name;
                            }}
                            .renderDescription=${(flow: Flow): string => {
                                return flow.slug;
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
