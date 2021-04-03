import { FlowDesignationEnum, FlowsApi, AuthenticatorTOTPStage, StagesApi } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { Form } from "../../../elements/forms/Form";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";
import "../../../elements/forms/FormGroup";
import { until } from "lit-html/directives/until";

@customElement("ak-stage-authenticator-totp-form")
export class AuthenticatorTOTPStageForm extends Form<AuthenticatorTOTPStage> {

    set stageUUID(value: string) {
        new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorTotpRead({
            stageUuid: value,
        }).then(stage => {
            this.stage = stage;
        });
    }

    @property({attribute: false})
    stage?: AuthenticatorTOTPStage;

    getSuccessMessage(): string {
        if (this.stage) {
            return t`Successfully updated stage.`;
        } else {
            return t`Successfully created stage.`;
        }
    }

    send = (data: AuthenticatorTOTPStage): Promise<AuthenticatorTOTPStage> => {
        if (this.stage) {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorTotpUpdate({
                stageUuid: this.stage.pk || "",
                data: data
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorTotpCreate({
                data: data
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${t`Name`}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.stage?.name || "")}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header">
                    ${t`Stage-specific settings`}
                </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Digits`}
                        ?required=${true}
                        name="digits">
                        <select name="users" class="pf-c-form-control">
                            <option value="6" ?selected=${this.stage?.digits === 6}>
                                ${t`6 digits, widely compatible`}
                            </option>
                            <option value="8" ?selected=${this.stage?.digits === 8}>
                                ${t`8 digits, not compatible with apps like Google Authenticator`}
                            </option>
                        </select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Configuration flow`}
                        name="configureFlow">
                        <select class="pf-c-form-control">
                            <option value="" ?selected=${this.stage?.configureFlow === undefined}>---------</option>
                            ${until(new FlowsApi(DEFAULT_CONFIG).flowsInstancesList({
                                ordering: "pk",
                                designation: FlowDesignationEnum.StageConfiguration,
                            }).then(flows => {
                                return flows.results.map(flow => {
                                    let selected = this.stage?.configureFlow === flow.pk;
                                    if (!this.stage?.configureFlow && flow.slug === "default-otp-time-configure") {
                                        selected = true;
                                    }
                                    return html`<option value=${ifDefined(flow.pk)} ?selected=${selected}>${flow.name} (${flow.slug})</option>`;
                                });
                            }), html`<option>${t`Loading...`}</option>`)}
                        </select>
                        <p class="pf-c-form__helper-text">${t`Flow used by an authenticated user to configure this Stage. If empty, user will not be able to configure this stage.`}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }

}
