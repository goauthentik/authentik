import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import {
    AuthTypeEnum,
    AuthenticatorSMSStage,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    ProviderEnum,
    StagesApi,
} from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../../api/Config";
import "../../../elements/forms/FormGroup";
import "../../../elements/forms/HorizontalFormElement";
import { ModelForm } from "../../../elements/forms/ModelForm";

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
    provider?: ProviderEnum;

    @property({ attribute: false })
    authType?: AuthTypeEnum;

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated stage.`;
        } else {
            return t`Successfully created stage.`;
        }
    }

    send = (data: AuthenticatorSMSStage): Promise<AuthenticatorSMSStage> => {
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
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`Stage used to configure an SMS-based TOTP authenticator.`}
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
                            value="${ifDefined(this.instance?.fromNumber || "")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Number the SMS will be sent from.`}
                        </p>
                    </ak-form-element-horizontal>

                    <ak-form-element-horizontal
                        label=${t`Twilio Account SID`}
                        ?hidden=${this.provider !== ProviderEnum.Twilio}
                        ?required=${true}
                        name="accountSid"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.accountSid || "")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Get this value from https://console.twilio.com`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Twilio Auth Token`}
                        ?hidden=${this.provider !== ProviderEnum.Twilio}
                        ?required=${true}
                        name="auth"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.auth || "")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Get this value from https://console.twilio.com`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Authentication Type`}
                        ?hidden=${this.provider !== ProviderEnum.Generic}
                        @change=${(ev: Event) => {
                            const current = (ev.target as HTMLInputElement).value;
                            this.authType = current as AuthTypeEnum;
                        }}
                        ?required=${true}
                        name="authType"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value="${AuthTypeEnum.Basic}"
                                ?selected=${this.instance?.authType === AuthTypeEnum.Basic}
                            >
                                ${t`Basic Auth`}
                            </option>
                            <option
                                value="${AuthTypeEnum.Bearer}"
                                ?selected=${this.instance?.authType === AuthTypeEnum.Bearer}
                            >
                                ${t`Bearer Token`}
                            </option>
                        </select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`External API URL`}
                        ?hidden=${this.provider !== ProviderEnum.Generic}
                        ?required=${true}
                        name="accountSid"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.accountSid || "")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`This is the full endpoint to send POST requests to.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`API Auth Username`}
                        ?hidden=${this.provider !== ProviderEnum.Generic}
                        ?required=${true}
                        name="auth"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.auth || "")}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`This is the username to be used with basic auth or the token when used with bearer token`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`API Auth password`}
                        ?hidden=${!(
                            this.provider === ProviderEnum.Generic &&
                            this.authType === AuthTypeEnum.Basic
                        )}
                        ?required=${false}
                        name="authPassword"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.authPassword)}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`This is the password to be used with basic auth`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`Configuration flow`} name="configureFlow">
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
                                html`<option>${t`Loading...`}</option>`,
                            )}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${t`Flow used by an authenticated user to configure this Stage. If empty, user will not be able to configure this stage.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
