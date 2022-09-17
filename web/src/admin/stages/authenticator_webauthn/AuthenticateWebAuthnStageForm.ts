import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import {
    AuthenticateWebAuthnStage,
    AuthenticatorAttachmentEnum,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
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
            return msg("Successfully updated stage.");
        } else {
            return msg("Successfully created stage.");
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
                ${msg(
                    "Stage used to configure a WebAutnn authenticator (i.e. Yubikey, FaceID/Windows Hello).",
                )}
            </div>
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Stage-specific settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("User verification")}
                        ?required=${true}
                        name="userVerification"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value="${UserVerificationEnum.Required}"
                                ?selected=${this.instance?.userVerification ===
                                UserVerificationEnum.Required}
                            >
                                ${msg("User verification must occur.")}
                            </option>
                            <option
                                value="${UserVerificationEnum.Preferred}"
                                ?selected=${this.instance?.userVerification ===
                                UserVerificationEnum.Preferred}
                            >
                                ${msg(
                                    "User verification is preferred if available, but not required.",
                                )}
                            </option>
                            <option
                                value="${UserVerificationEnum.Discouraged}"
                                ?selected=${this.instance?.userVerification ===
                                UserVerificationEnum.Discouraged}
                            >
                                ${msg("User verification should not occur.")}
                            </option>
                        </select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Resident key requirement")}
                        ?required=${true}
                        name="residentKeyRequirement"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value="${ResidentKeyRequirementEnum.Discouraged}"
                                ?selected=${this.instance?.residentKeyRequirement ===
                                ResidentKeyRequirementEnum.Discouraged}
                            >
                                ${msg("The authenticator should not create a dedicated credential")}
                            </option>
                            <option
                                value="${ResidentKeyRequirementEnum.Preferred}"
                                ?selected=${this.instance?.residentKeyRequirement ===
                                ResidentKeyRequirementEnum.Preferred}
                            >
                                ${msg(
                                    "The authenticator can create and store a dedicated credential, but if it doesn't that's alright too",
                                )}
                            </option>
                            <option
                                value="${ResidentKeyRequirementEnum.Required}"
                                ?selected=${this.instance?.residentKeyRequirement ===
                                ResidentKeyRequirementEnum.Required}
                            >
                                ${msg(
                                    "The authenticator MUST create a dedicated credential. If it cannot, the RP is prepared for an error to occur",
                                )}
                            </option>
                        </select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Authenticator Attachment")}
                        ?required=${true}
                        name="authenticatorAttachment"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value=""
                                ?selected=${this.instance?.authenticatorAttachment === null}
                            >
                                ${msg("No preference is sent")}
                            </option>
                            <option
                                value="${AuthenticatorAttachmentEnum.Platform}"
                                ?selected=${this.instance?.authenticatorAttachment ===
                                AuthenticatorAttachmentEnum.Platform}
                            >
                                ${msg(
                                    "A non-removable authenticator, like TouchID or Windows Hello",
                                )}
                            </option>
                            <option
                                value="${AuthenticatorAttachmentEnum.CrossPlatform}"
                                ?selected=${this.instance?.authenticatorAttachment ===
                                AuthenticatorAttachmentEnum.CrossPlatform}
                            >
                                ${msg('A "roaming" authenticator, like a YubiKey')}
                            </option>
                        </select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Configuration flow")}
                        name="configureFlow"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value=""
                                ?selected=${this.instance?.configureFlow === undefined}
                            >
                                ---------
                            </option>
                            ${until(
                                new FlowsApi(DEFAULT_CONFIG)
                                    .flowsInstancesList({
                                        ordering: "slug",
                                        designation:
                                            FlowsInstancesListDesignationEnum.StageConfiguration,
                                    })
                                    .then((flows) => {
                                        return flows.results.map((flow) => {
                                            let selected = this.instance?.configureFlow === flow.pk;
                                            if (
                                                !this.instance?.pk &&
                                                !this.instance?.configureFlow &&
                                                flow.slug === "default-otp-time-configure"
                                            ) {
                                                selected = true;
                                            }
                                            return html`<option
                                                value=${ifDefined(flow.pk)}
                                                ?selected=${selected}
                                            >
                                                ${flow.name} (${flow.slug})
                                            </option>`;
                                        });
                                    }),
                                html`<option>${msg("Loading...")}</option>`,
                            )}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Flow used by an authenticated user to configure this Stage. If empty, user will not be able to configure this stage.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
