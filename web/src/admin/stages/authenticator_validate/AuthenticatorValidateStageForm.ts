import { BaseStageForm } from "@goauthentik/admin/stages/BaseStageForm";
import { deviceTypeRestrictionPair } from "@goauthentik/admin/stages/authenticator_webauthn/utils";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/Alert";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-dynamic-selected-provider.js";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-provider";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/utils/TimeDeltaHelp";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    AuthenticatorValidateStage,
    DeviceClassesEnum,
    NotConfiguredActionEnum,
    PaginatedStageList,
    StagesApi,
    UserVerificationEnum,
} from "@goauthentik/api";

import {
    authenticatorWebauthnDeviceTypesListProvider,
    stagesProvider,
    stagesSelector,
} from "./AuthenticatorValidateStageFormHelpers.js";

@customElement("ak-stage-authenticator-validate-form")
export class AuthenticatorValidateStageForm extends BaseStageForm<AuthenticatorValidateStage> {
    async loadInstance(pk: string): Promise<AuthenticatorValidateStage> {
        const stage = await new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorValidateRetrieve({
            stageUuid: pk,
        });
        this.showConfigurationStages =
            stage.notConfiguredAction === NotConfiguredActionEnum.Configure;
        return stage;
    }

    async load(): Promise<void> {
        this.stages = await new StagesApi(DEFAULT_CONFIG).stagesAllList({
            ordering: "name",
        });
    }

    stages?: PaginatedStageList;

    @property({ type: Boolean })
    showConfigurationStages = true;

    async send(data: AuthenticatorValidateStage): Promise<AuthenticatorValidateStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorValidateUpdate({
                stageUuid: this.instance.pk || "",
                authenticatorValidateStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorValidateCreate({
                authenticatorValidateStageRequest: data,
            });
        }
    }

    isDeviceClassSelected(field: DeviceClassesEnum): boolean {
        return (
            (this.instance?.deviceClasses || []).filter((isField) => {
                return field === isField;
            }).length > 0
        );
    }

    renderForm(): TemplateResult {
        const authenticators = [
            [DeviceClassesEnum.Static, msg("Static Tokens")],
            [DeviceClassesEnum.Totp, msg("TOTP Authenticators")],
            [DeviceClassesEnum.Webauthn, msg("WebAuthn Authenticators")],
            [DeviceClassesEnum.Duo, msg("Duo Authenticators")],
            [DeviceClassesEnum.Sms, msg("SMS-based Authenticators")],
            [DeviceClassesEnum.Email, msg("Email-based Authenticators")],
        ];

        return html`
            <span>
                ${msg(
                    "Stage used to validate any authenticator. This stage should be used during authentication or authorization flows.",
                )}
            </span>
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
                        label=${msg("Device classes")}
                        ?required=${true}
                        name="deviceClasses"
                    >
                        <ak-checkbox-group
                            name="users"
                            class="user-field-select"
                            .options=${authenticators}
                            .value=${authenticators
                                .map((authenticator) => authenticator[0])
                                .filter((name) =>
                                    this.isDeviceClassSelected(name as DeviceClassesEnum),
                                )}
                        ></ak-checkbox-group>
                        <p class="pf-c-form__helper-text">
                            ${msg("Device classes which can be used to authenticate.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Last validation threshold")}
                        ?required=${true}
                        name="lastAuthThreshold"
                    >
                        <input
                            type="text"
                            value="${this.instance?.lastAuthThreshold || "seconds=0"}"
                            class="pf-c-form-control pf-m-monospace"
                            autocomplete="off"
                            spellcheck="false"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "If the user has successfully authenticated with a device in the classes listed above within this configured duration, this stage will be skipped.",
                            )}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Not configured action")}
                        ?required=${true}
                        name="notConfiguredAction"
                    >
                        <select
                            class="pf-c-form-control"
                            @change=${(ev: Event) => {
                                const target = ev.target as HTMLSelectElement;
                                if (
                                    target.selectedOptions[0].value ===
                                    NotConfiguredActionEnum.Configure
                                ) {
                                    this.showConfigurationStages = true;
                                } else {
                                    this.showConfigurationStages = false;
                                }
                            }}
                        >
                            <option
                                value=${NotConfiguredActionEnum.Configure}
                                ?selected=${this.instance?.notConfiguredAction ===
                                NotConfiguredActionEnum.Configure}
                            >
                                ${msg("Force the user to configure an authenticator")}
                            </option>
                            <option
                                value=${NotConfiguredActionEnum.Deny}
                                ?selected=${this.instance?.notConfiguredAction ===
                                NotConfiguredActionEnum.Deny}
                            >
                                ${msg("Deny the user access")}
                            </option>
                            <option
                                value=${NotConfiguredActionEnum.Skip}
                                ?selected=${this.instance?.notConfiguredAction ===
                                NotConfiguredActionEnum.Skip}
                            >
                                ${msg("Continue")}
                            </option>
                        </select>
                    </ak-form-element-horizontal>
                    ${this.showConfigurationStages
                        ? html`
                              <ak-form-element-horizontal
                                  label=${msg("Configuration stages")}
                                  name="configurationStages"
                              >
                                  <ak-dual-select-dynamic-selected
                                      .provider=${stagesProvider}
                                      .selector=${stagesSelector(
                                          this.instance?.configurationStages,
                                      )}
                                      available-label="${msg("Available Stages")}"
                                      selected-label="${msg("Selected Stages")}"
                                  ></ak-dual-select-dynamic-selected>
                                  <p class="pf-c-form__helper-text">
                                      ${msg(
                                          "Stages used to configure Authenticator when user doesn't have any compatible devices. After this configuration Stage passes, the user is not prompted again.",
                                      )}
                                  </p>
                                  <p class="pf-c-form__helper-text">
                                      ${msg(
                                          "When multiple stages are selected, the user can choose which one they want to enroll.",
                                      )}
                                  </p>
                              </ak-form-element-horizontal>
                          `
                        : html``}
                </div>
            </ak-form-group>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("WebAuthn-specific settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("WebAuthn User verification")}
                        ?required=${true}
                        name="webauthnUserVerification"
                    >
                        <ak-radio
                            .options=${[
                                {
                                    label: msg("User verification must occur."),
                                    value: UserVerificationEnum.Required,
                                    default: true,
                                },
                                {
                                    label: msg(
                                        "User verification is preferred if available, but not required.",
                                    ),
                                    value: UserVerificationEnum.Preferred,
                                },
                                {
                                    label: msg("User verification should not occur."),
                                    value: UserVerificationEnum.Discouraged,
                                },
                            ]}
                            .value=${this.instance?.webauthnUserVerification}
                        >
                        </ak-radio>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("WebAuthn Device type restrictions")}
                        name="webauthnAllowedDeviceTypes"
                    >
                        <ak-dual-select-provider
                            .provider=${authenticatorWebauthnDeviceTypesListProvider}
                            .selected=${(this.instance?.webauthnAllowedDeviceTypesObj ?? []).map(
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
                        <ak-alert ?inline=${true}>
                            ${
                                /* TODO: Remove this after 2024.6..or maybe later? */
                                msg(
                                    "This restriction only applies to devices created in authentik 2024.4 or later.",
                                )
                            }
                        </ak-alert>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-validate-form": AuthenticatorValidateStageForm;
    }
}
