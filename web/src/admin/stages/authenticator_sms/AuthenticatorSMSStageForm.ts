import { RenderFlowOption } from "@goauthentik/admin/flows/utils";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import {
    AuthTypeEnum,
    AuthenticatorSMSStage,
    Flow,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    FlowsInstancesListRequest,
    NotificationWebhookMapping,
    PropertymappingsApi,
    PropertymappingsNotificationListRequest,
    ProviderEnum,
    StagesApi,
} from "@goauthentik/api";

@customElement("ak-stage-authenticator-sms-form")
export class AuthenticatorSMSStageForm extends ModelForm<AuthenticatorSMSStage, string> {
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

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated stage.`;
        } else {
            return t`Successfully created stage.`;
        }
    }

    async send(data: AuthenticatorSMSStage): Promise<AuthenticatorSMSStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorSmsUpdate({
                stageUuid: this.instance.pk || "",
                authenticatorSMSStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorSmsCreate({
                authenticatorSMSStageRequest: data,
            });
        }
    }

    renderProviderTwillio(): TemplateResult {
        return html` <ak-form-element-horizontal
                label=${t`Twilio Account SID`}
                ?required=${true}
                name="accountSid"
            >
                <input
                    type="text"
                    value="${first(this.instance?.accountSid, "")}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${t`Get this value from https://console.twilio.com`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Twilio Auth Token`} ?required=${true} name="auth">
                <input
                    type="text"
                    value="${first(this.instance?.auth, "")}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${t`Get this value from https://console.twilio.com`}
                </p>
            </ak-form-element-horizontal>`;
    }

    renderProviderGeneric(): TemplateResult {
        return html`
            <ak-form-element-horizontal
                label=${t`Authentication Type`}
                @change=${(ev: Event) => {
                    const current = (ev.target as HTMLInputElement).value;
                    this.authType = current as AuthTypeEnum;
                }}
                ?required=${true}
                name="authType"
            >
                <ak-radio
                    .options=${[
                        {
                            label: t`Basic Auth`,
                            value: AuthTypeEnum.Basic,
                            default: true,
                        },
                        {
                            label: t`Bearer Token`,
                            value: AuthTypeEnum.Bearer,
                        },
                    ]}
                    .value=${this.instance?.authType}
                >
                </ak-radio>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`External API URL`}
                ?required=${true}
                name="accountSid"
            >
                <input
                    type="text"
                    value="${first(this.instance?.accountSid, "")}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${t`This is the full endpoint to send POST requests to.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`API Auth Username`} ?required=${true} name="auth">
                <input
                    type="text"
                    value="${first(this.instance?.auth, "")}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">
                    ${t`This is the username to be used with basic auth or the token when used with bearer token`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`API Auth password`}
                ?required=${false}
                name="authPassword"
            >
                <input
                    type="text"
                    value="${first(this.instance?.authPassword, "")}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">
                    ${t`This is the password to be used with basic auth`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Mapping`} name="mapping">
                <ak-search-select
                    .fetchObjects=${async (
                        query?: string,
                    ): Promise<NotificationWebhookMapping[]> => {
                        const args: PropertymappingsNotificationListRequest = {
                            ordering: "saml_name",
                        };
                        if (query !== undefined) {
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
                    .value=${(item: NotificationWebhookMapping | undefined): string | undefined => {
                        return item?.pk;
                    }}
                    .selected=${(item: NotificationWebhookMapping): boolean => {
                        return this.instance?.mapping === item.pk;
                    }}
                    ?blankable=${true}
                >
                </ak-search-select>
                <p class="pf-c-form__helper-text">
                    ${t`Modify the payload sent to the custom provider.`}
                </p>
            </ak-form-element-horizontal>
        `;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`Stage used to configure an SMS-based TOTP authenticator.`}
            </div>
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${first(this.instance?.name, "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Authenticator type name`}
                ?required=${false}
                name="friendlyName"
            >
                <input
                    type="text"
                    value="${first(this.instance?.friendlyName, "")}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">
                    ${t`Display name of this authenticator, used by users when they enroll an authenticator.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${t`Stage-specific settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Provider`}
                        ?required=${true}
                        name="provider"
                    >
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
                                ${t`Twilio`}
                            </option>
                            <option
                                value="${ProviderEnum.Generic}"
                                ?selected=${this.instance?.provider === ProviderEnum.Generic}
                            >
                                ${t`Generic`}
                            </option>
                        </select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`From number`}
                        ?required=${true}
                        name="fromNumber"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.fromNumber, "")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Number the SMS will be sent from.`}
                        </p>
                    </ak-form-element-horizontal>
                    ${this.provider === ProviderEnum.Generic
                        ? this.renderProviderGeneric()
                        : this.renderProviderTwillio()}
                    <ak-form-element-horizontal name="verifyOnly">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.verifyOnly, false)}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${t`Hash phone number`}</span>
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${t`If enabled, only a hash of the phone number will be saved. This can be done for data-protection reasons. Devices created from a stage with this enabled cannot be used with the authenticator validation stage.`}
                        </p>
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
                            ${t`Flow used by an authenticated user to configure this Stage. If empty, user will not be able to configure this stage.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
