import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
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

@customElement("ak-stage-authenticator-validate-form")
export class AuthenticatorValidateStageForm extends ModelForm<AuthenticatorValidateStage, string> {
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

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated stage.");
        } else {
            return msg("Successfully created stage.");
        }
    }

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
        return html`<form class="pf-c-form pf-m-horizontal">
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
                        <select name="users" class="pf-c-form-control" multiple>
                            <option
                                value=${DeviceClassesEnum.Static}
                                ?selected=${this.isDeviceClassSelected(DeviceClassesEnum.Static)}
                            >
                                ${msg("Static Tokens")}
                            </option>
                            <option
                                value=${DeviceClassesEnum.Totp}
                                ?selected=${this.isDeviceClassSelected(DeviceClassesEnum.Totp)}
                            >
                                ${msg("TOTP Authenticators")}
                            </option>
                            <option
                                value=${DeviceClassesEnum.Webauthn}
                                ?selected=${this.isDeviceClassSelected(DeviceClassesEnum.Webauthn)}
                            >
                                ${msg("WebAuthn Authenticators")}
                            </option>
                            <option
                                value=${DeviceClassesEnum.Duo}
                                ?selected=${this.isDeviceClassSelected(DeviceClassesEnum.Duo)}
                            >
                                ${msg("Duo Authenticators")}
                            </option>
                            <option
                                value=${DeviceClassesEnum.Sms}
                                ?selected=${this.isDeviceClassSelected(DeviceClassesEnum.Sms)}
                            >
                                ${msg("SMS-based Authenticators")}
                            </option>
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${msg("Device classes which can be used to authenticate.")}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${msg("Hold control/command to select multiple items.")}
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
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "If any of the devices user of the types selected above have been used within this duration, this stage will be skipped.",
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
                    ${this.showConfigurationStages
                        ? html`
                              <ak-form-element-horizontal
                                  label=${msg("Configuration stages")}
                                  name="configurationStages"
                              >
                                  <select class="pf-c-form-control" multiple>
                                      ${this.stages?.results.map((stage) => {
                                          const selected = Array.from(
                                              this.instance?.configurationStages || [],
                                          ).some((su) => {
                                              return su == stage.pk;
                                          });
                                          return html`<option
                                              value=${ifDefined(stage.pk)}
                                              ?selected=${selected}
                                          >
                                              ${stage.name} (${stage.verboseName})
                                          </option>`;
                                      })}
                                  </select>
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
        </form>`;
    }
}
