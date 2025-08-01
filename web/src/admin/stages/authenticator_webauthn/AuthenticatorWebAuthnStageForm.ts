import "#components/ak-number-input";
import "#elements/ak-dual-select/ak-dual-select-provider";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { DataProvision } from "#elements/ak-dual-select/types";

import { RenderFlowOption } from "#admin/flows/utils";
import { deviceTypeRestrictionPair } from "#admin/stages/authenticator_webauthn/utils";
import { BaseStageForm } from "#admin/stages/BaseStageForm";

import {
    AuthenticatorAttachmentEnum,
    AuthenticatorWebAuthnStage,
    Flow,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    FlowsInstancesListRequest,
    ResidentKeyRequirementEnum,
    StagesApi,
    UserVerificationEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-stage-authenticator-webauthn-form")
export class AuthenticatorWebAuthnStageForm extends BaseStageForm<AuthenticatorWebAuthnStage> {
    async loadInstance(pk: string): Promise<AuthenticatorWebAuthnStage> {
        return await new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorWebauthnRetrieve({
            stageUuid: pk,
        });
    }

    async send(data: AuthenticatorWebAuthnStage): Promise<AuthenticatorWebAuthnStage> {
        if (data.authenticatorAttachment?.toString() === "") {
            data.authenticatorAttachment = null;
        }
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorWebauthnUpdate({
                stageUuid: this.instance.pk || "",
                authenticatorWebAuthnStageRequest: data,
            });
        }
        return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorWebauthnCreate({
            authenticatorWebAuthnStageRequest: data,
        });
    }

    renderForm(): TemplateResult {
        return html` <span>
                ${msg(
                    "Stage used to configure a WebAuthn authenticator (i.e. Yubikey, FaceID/Windows Hello).",
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
            <ak-form-group open label="${msg("Stage-specific settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("User verification")}
                        required
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
                        required
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
                        required
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
                    <ak-number-input
                        label=${msg("Maximum registration attempts")}
                        required
                        name="maxAttempts"
                        value="${this.instance?.maxAttempts || 0}"
                        help=${msg(
                            "Maximum allowed registration attempts. When set to 0 attempts, attempts are not limited.",
                        )}
                    ></ak-number-input>
                    <ak-form-element-horizontal
                        label=${msg("Device type restrictions")}
                        name="deviceTypeRestrictions"
                    >
                        <ak-dual-select-provider
                            .provider=${(page: number, search?: string): Promise<DataProvision> => {
                                return new StagesApi(DEFAULT_CONFIG)
                                    .stagesAuthenticatorWebauthnDeviceTypesList({
                                        page: page,
                                        search: search,
                                    })
                                    .then((results) => {
                                        return {
                                            pagination: results.pagination,
                                            options: results.results.map(deviceTypeRestrictionPair),
                                        };
                                    });
                            }}
                            .selected=${(this.instance?.deviceTypeRestrictionsObj ?? []).map(
                                deviceTypeRestrictionPair,
                            )}
                            available-label="${msg("Available Device types")}"
                            selected-label="${msg("Selected Device types")}"
                        ></ak-dual-select-provider>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Optionally restrict which WebAuthn device types may be used. When no device types are selected, all devices are allowed.",
                            )}
                        </p>
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
        "ak-stage-authenticator-webauthn-form": AuthenticatorWebAuthnStageForm;
    }
}
