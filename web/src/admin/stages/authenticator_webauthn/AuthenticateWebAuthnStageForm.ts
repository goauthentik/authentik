import { RenderFlowOption } from "@goauthentik/admin/flows/utils";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

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
            return msg("Successfully updated stage.");
        } else {
            return msg("Successfully created stage.");
        }
    }

    async send(data: AuthenticateWebAuthnStage): Promise<AuthenticateWebAuthnStage> {
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
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <span>
                ${msg(
                    "Stage used to configure a WebAutnn authenticator (i.e. Yubikey, FaceID/Windows Hello).",
                )}
            </span>
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${first(this.instance?.name, "")}"
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
                    value="${first(this.instance?.friendlyName, "")}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Display name of this authenticator, used by users when they enroll an authenticator.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Stage-specific settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("User verification")}
                        ?required=${true}
                        name="userVerification"
                    >
                        <ak-radio
                            .options=${[
                                {
                                    label: msg("Required: User verification must occur."),
                                    value: UserVerificationEnum.Required,
                                    default: true,
                                },
                                {
                                    label: msg(
                                        "Preferred: User verification is preferred if available, but not required.",
                                    ),
                                    value: UserVerificationEnum.Preferred,
                                },
                                {
                                    label: msg("Discouraged: User verification should not occur."),
                                    value: UserVerificationEnum.Discouraged,
                                },
                            ]}
                            .value=${this.instance?.userVerification}
                        >
                        </ak-radio>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Resident key requirement")}
                        ?required=${true}
                        name="residentKeyRequirement"
                    >
                        <ak-radio
                            .options=${[
                                {
                                    label: msg(
                                        "Required: The authenticator MUST create a dedicated credential. If it cannot, the RP is prepared for an error to occur",
                                    ),
                                    value: ResidentKeyRequirementEnum.Required,
                                    default: true,
                                },
                                {
                                    label: msg(
                                        "Preferred: The authenticator can create and store a dedicated credential, but if it doesn't that's alright too",
                                    ),
                                    value: ResidentKeyRequirementEnum.Preferred,
                                },
                                {
                                    label: msg(
                                        "Discouraged: The authenticator should not create a dedicated credential",
                                    ),
                                    value: ResidentKeyRequirementEnum.Discouraged,
                                },
                            ]}
                            .value=${this.instance?.residentKeyRequirement}
                        >
                        </ak-radio>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Authenticator Attachment")}
                        ?required=${true}
                        name="authenticatorAttachment"
                    >
                        <ak-radio
                            .options=${[
                                {
                                    label: msg("No preference is sent"),
                                    value: null,
                                    default: true,
                                },
                                {
                                    label: msg(
                                        "A non-removable authenticator, like TouchID or Windows Hello",
                                    ),
                                    value: AuthenticatorAttachmentEnum.Platform,
                                },
                                {
                                    label: msg('A "roaming" authenticator, like a YubiKey'),
                                    value: AuthenticatorAttachmentEnum.CrossPlatform,
                                },
                            ]}
                            .value=${this.instance?.authenticatorAttachment}
                        >
                        </ak-radio>
                    </ak-form-element-horizontal>
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
                            ?blankable=${true}
                        >
                        </ak-search-select>
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
