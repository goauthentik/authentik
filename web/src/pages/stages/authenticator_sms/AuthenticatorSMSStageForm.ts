import { t } from "@lingui/macro";

import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators";
import { ifDefined } from "lit/directives/if-defined";
import { until } from "lit/directives/until";

import {
    FlowsApi,
    AuthenticatorTOTPStage,
    StagesApi,
    FlowsInstancesListDesignationEnum,
    AuthenticatorSMSStage,
    ProviderEnum,
} from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../../api/Config";
import "../../../elements/forms/FormGroup";
import "../../../elements/forms/HorizontalFormElement";
import { ModelForm } from "../../../elements/forms/ModelForm";

@customElement("ak-stage-authenticator-sms-form")
export class AuthenticatorSMSStageForm extends ModelForm<AuthenticatorSMSStage, string> {
    loadInstance(pk: string): Promise<AuthenticatorSMSStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorSmsRetrieve({
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
                        <select name="users" class="pf-c-form-control">
                            <option
                                value="${ProviderEnum.Twilio}"
                                ?selected=${this.instance?.provider === ProviderEnum.Twilio}
                            >
                                ${t`Twilio`}
                            </option>
                        </select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Twilio Account SID`}
                        ?required=${true}
                        name="twilioAccountSid"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.twilioAccountSid || "")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Get this value from https://console.twilio.com`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Twilio Auth Token`}
                        ?required=${true}
                        name="twilioAuth"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.twilioAuth || "")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Get this value from https://console.twilio.com`}
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
                                        ordering: "pk",
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
