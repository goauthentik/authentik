import "#components/ak-switch-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKLabel } from "#components/ak-label";

import { RenderFlowOption } from "#admin/flows/utils";
import { BaseStageForm } from "#admin/stages/BaseStageForm";

import {
    AuthenticatorSMSStage,
    AuthTypeEnum,
    Flow,
    FlowDesignationEnum,
    FlowsApi,
    FlowsInstancesListRequest,
    NotificationWebhookMapping,
    PropertymappingsApi,
    PropertymappingsNotificationListRequest,
    ProviderEnum,
    StagesApi,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-stage-authenticator-sms-form")
export class AuthenticatorSMSStageForm extends BaseStageForm<AuthenticatorSMSStage> {
    loadInstance(pk: string): Promise<AuthenticatorSMSStage> {
        return new StagesApi(DEFAULT_CONFIG)
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
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorSmsUpdate({
                stageUuid: this.instance.pk || "",
                authenticatorSMSStageRequest: data,
            });
        }
        return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorSmsCreate({
            authenticatorSMSStageRequest: data,
        });
    }

    renderProviderTwillio(): TemplateResult {
        return html` <ak-form-element-horizontal required name="accountSid">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "accountSid",
                        required: true,
                    },
                    msg("Twilio Account SID"),
                )}
                <input
                    id="accountSid"
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
            <ak-form-element-horizontal required name="auth">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "auth",
                        required: true,
                    },
                    msg("Twilio Auth Token"),
                )}
                <input
                    id="auth"
                    type="text"
                    value="${this.instance?.auth ?? ""}"
                    class="pf-c-form-control pf-m-monospace"
                    autocomplete="off"
                    spellcheck="false"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg("Get this value from https://console.twilio.com")}
                </p>
            </ak-form-element-horizontal>`;
    }

    renderProviderGeneric(): TemplateResult {
        return html`
            <ak-form-element-horizontal
                @change=${(ev: Event) => {
                    const current = (ev.target as HTMLInputElement).value;
                    this.authType = current as AuthTypeEnum;
                }}
                required
                name="authType"
            >
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "authType",
                        required: true,
                    },
                    msg("Authentication Type"),
                )}
                <ak-radio
                    id="authType"
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
            <ak-form-element-horizontal required name="accountSid">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "accountSid",
                        required: true,
                    },
                    msg("External API URL"),
                )}
                <input
                    id="accountSid"
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
            <ak-form-element-horizontal required name="auth">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "auth",
                        required: true,
                    },
                    msg("API Auth Username"),
                )}
                <input
                    id="auth"
                    type="text"
                    value="${this.instance?.auth ?? ""}"
                    class="pf-c-form-control pf-m-monospace"
                    autocomplete="off"
                    spellcheck="false"
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "This is the username to be used with basic auth or the token when used with bearer token",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal ?required=${false} name="authPassword">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "authPassword",
                    },
                    msg("API Auth password"),
                )}
                <input
                    id="authPassword"
                    type="text"
                    value="${this.instance?.authPassword ?? ""}"
                    class="pf-c-form-control pf-m-monospace"
                    autocomplete="off"
                    spellcheck="false"
                />
                <p class="pf-c-form__helper-text">
                    ${msg("This is the password to be used with basic auth")}
                </p>
            </ak-form-element-horizontal>
        `;
    }

    protected override renderForm(): TemplateResult {
        return html` <span>
                ${msg("Stage used to configure an SMS-based TOTP authenticator.")}
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
                    <ak-form-element-horizontal required name="provider">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "provider",
                                required: true,
                            },
                            msg("Provider"),
                        )}
                        <select
                            id="provider"
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
                    <ak-form-element-horizontal required name="fromNumber">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "fromNumber",
                                required: true,
                            },
                            msg("From number"),
                        )}
                        <input
                            id="fromNumber"
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
                    ${this.provider === ProviderEnum.Generic
                        ? this.renderProviderGeneric()
                        : this.renderProviderTwillio()}
                    <ak-form-element-horizontal name="mapping">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "mapping",
                            },
                            msg("Mapping"),
                        )}
                        <ak-search-select
                            id="mapping"
                            .fetchObjects=${async (
                                query?: string,
                            ): Promise<NotificationWebhookMapping[]> => {
                                const args: PropertymappingsNotificationListRequest = {
                                    ordering: "name",
                                };
                                if (query) {
                                    args.search = query;
                                }
                                const items = await new PropertymappingsApi(
                                    DEFAULT_CONFIG,
                                ).propertymappingsNotificationList(args);
                                return items.results;
                            }}
                            .renderElement=${(item: NotificationWebhookMapping): string => {
                                return item.name;
                            }}
                            .value=${(item?: NotificationWebhookMapping) => {
                                return item?.pk;
                            }}
                            .selected=${(item: NotificationWebhookMapping): boolean => {
                                return this.instance?.mapping === item.pk;
                            }}
                            blankable
                        >
                        </ak-search-select>
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
        "ak-stage-authenticator-sms-form": AuthenticatorSMSStageForm;
    }
}
