import "#components/ak-secret-text-input";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import { aki } from "#common/api/client";

import { AKSearchSelect } from "#components/ak-search-select-field";

import { AKFlowSearch } from "#admin/common/ak-flow-search/AKFlowSearch";
import { notificationMappingSource } from "#admin/common/search-sources";
import { BaseStageForm } from "#admin/stages/BaseStageForm";

import {
    AuthenticatorSMSStage,
    AuthenticatorSMSStageRequest,
    AuthTypeEnum,
    FlowDesignationEnum,
    ProviderEnum,
    StagesApi,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-stage-authenticator-sms-form")
export class AuthenticatorSMSStageForm extends BaseStageForm<AuthenticatorSMSStage> {
    loadInstance(pk: string): Promise<AuthenticatorSMSStage> {
        return aki(StagesApi)
            .stagesAuthenticatorSmsRetrieve({
                stageUuid: pk,
            })
            .then((stage) => {
                this.provider = stage.provider;
                this.authType = stage.authType;

                return stage;
            });
    }

    @property({ attribute: false })
    provider: ProviderEnum = ProviderEnum.Twilio;

    @property({ attribute: false })
    authType?: AuthTypeEnum;

    async send(data: AuthenticatorSMSStage): Promise<AuthenticatorSMSStage> {
        if (this.instance) {
            return aki(StagesApi).stagesAuthenticatorSmsPartialUpdate({
                stageUuid: this.instance.pk || "",
                patchedAuthenticatorSMSStageRequest: data,
            });
        }

        return aki(StagesApi).stagesAuthenticatorSmsCreate({
            authenticatorSMSStageRequest: data as unknown as AuthenticatorSMSStageRequest,
        });
    }

    renderProviderTwillio(): TemplateResult {
        return html` <ak-form-element-horizontal
                label=${msg("Twilio Account SID")}
                required
                name="accountSid"
            >
                <input
                    type="text"
                    value="${this.instance?.accountSid ?? ""}"
                    class="pf-c-form-control pf-m-monospace"
                    autocomplete="off"
                    spellcheck="false"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg("Get this value from https://console.twilio.com")}
                </p>
            </ak-form-element-horizontal>
            <ak-secret-text-input
                name="auth"
                label=${msg("Twilio Auth Token")}
                input-hint="code"
                ?required=${!this.instance}
                ?revealed=${!this.instance}
                help=${msg("Get this value from https://console.twilio.com")}
            ></ak-secret-text-input>`;
    }

    renderProviderGeneric(): TemplateResult {
        return html`
            <ak-form-element-horizontal
                label=${msg("Authentication Type")}
                @change=${(ev: Event) => {
                    const current = (ev.target as HTMLInputElement).value;
                    this.authType = current as AuthTypeEnum;
                }}
                required
                name="authType"
            >
                <ak-radio
                    .options=${[
                        {
                            label: msg("Basic Auth"),
                            value: AuthTypeEnum.Basic,
                            default: true,
                        },
                        {
                            label: msg("Bearer Token"),
                            value: AuthTypeEnum.Bearer,
                        },
                    ]}
                    .value=${this.instance?.authType}
                >
                </ak-radio>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("External API URL")} required name="accountSid">
                <input
                    type="text"
                    value="${this.instance?.accountSid ?? ""}"
                    class="pf-c-form-control pf-m-monospace"
                    autocomplete="off"
                    spellcheck="false"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg("This is the full endpoint to send POST requests to.")}
                </p>
            </ak-form-element-horizontal>
            <ak-secret-text-input
                name="auth"
                label=${msg("API Auth Username")}
                input-hint="code"
                ?required=${!this.instance}
                ?revealed=${!this.instance}
                help=${msg(
                    "This is the username to be used with basic auth or the token when used with bearer token",
                )}
            ></ak-secret-text-input>
            <ak-secret-text-input
                name="authPassword"
                label=${msg("API Auth password")}
                input-hint="code"
                ?revealed=${!this.instance}
                help=${msg("This is the password to be used with basic auth")}
            ></ak-secret-text-input>
        `;
    }

    protected override renderForm(): TemplateResult {
        return html` <span>
                ${msg("Stage used to configure an SMS-based TOTP authenticator.")}
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
                    <ak-form-element-horizontal label=${msg("Provider")} required name="provider">
                        <select
                            class="pf-c-form-control"
                            @change=${(ev: Event) => {
                                const current = (ev.target as HTMLInputElement).value;
                                this.provider = current as ProviderEnum;
                            }}
                        >
                            <option
                                value="${ProviderEnum.Twilio}"
                                ?selected=${this.instance?.provider === ProviderEnum.Twilio}
                            >
                                ${msg("Twilio")}
                            </option>
                            <option
                                value="${ProviderEnum.Generic}"
                                ?selected=${this.instance?.provider === ProviderEnum.Generic}
                            >
                                ${msg("Generic")}
                            </option>
                        </select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("From number")}
                        required
                        name="fromNumber"
                    >
                        <input
                            type="text"
                            value="${this.instance?.fromNumber ?? ""}"
                            class="pf-c-form-control pf-m-monospace"
                            autocomplete="off"
                            spellcheck="false"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Number the SMS will be sent from.")}
                        </p>
                    </ak-form-element-horizontal>
                    ${
                        this.provider === ProviderEnum.Generic
                            ? this.renderProviderGeneric()
                            : this.renderProviderTwillio()
                    }
                    <ak-form-element-horizontal label=${msg("Mapping")} name="mapping">
                        ${AKSearchSelect({
                            name: "mapping",
                            source: notificationMappingSource,
                            value: this.instance?.mapping,
                            blankable: true,
                        })}
                        <p class="pf-c-form__helper-text">
                            ${msg("Modify the payload sent to the provider.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-switch-input
                        name="verifyOnly"
                        label=${msg("Hash phone number")}
                        ?checked=${this.instance?.verifyOnly ?? false}
                        help=${msg(
                            "If enabled, only a hash of the phone number will be saved. This can be done for data-protection reasons. Devices created from a stage with this enabled cannot be used with the authenticator validation stage.",
                        )}
                    ></ak-switch-input>
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
        "ak-stage-authenticator-sms-form": AuthenticatorSMSStageForm;
    }
}
