import { FlowDesignationEnum, FlowsApi, AuthenticatorStaticStage, StagesApi } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { Form } from "../../../elements/forms/Form";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";
import "../../../elements/forms/FormGroup";
import { until } from "lit-html/directives/until";
import { first } from "../../../utils";

@customElement("ak-stage-authenticator-static-form")
export class AuthenticatorStaticStageForm extends Form<AuthenticatorStaticStage> {

    set stageUUID(value: string) {
        new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorStaticRead({
            stageUuid: value,
        }).then(stage => {
            this.stage = stage;
        });
    }

    @property({attribute: false})
    stage?: AuthenticatorStaticStage;

    getSuccessMessage(): string {
        if (this.stage) {
            return t`Successfully updated stage.`;
        } else {
            return t`Successfully created stage.`;
        }
    }

    send = (data: AuthenticatorStaticStage): Promise<AuthenticatorStaticStage> => {
        if (this.stage) {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorStaticUpdate({
                stageUuid: this.stage.pk || "",
                data: data
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesUserWriteCreate({
                data: data
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`Stage used to configure a static authenticator (i.e. static tokens). This stage should be used for configuration flows.`}
            </div>
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
                        label=${t`Token count`}
                        ?required=${true}
                        name="tokenCount">
                        <input type="text" value="${first(this.stage?.tokenCount, 6)}" class="pf-c-form-control" required>
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
                                    if (!this.stage?.pk && !this.stage?.configureFlow && flow.slug === "default-otp-time-configure") {
                                        selected = true;
                                    }
                                    return html`<option value=${ifDefined(flow.pk)} ?selected=${selected}>${flow.name} (${flow.slug})</option>`;
                                });
                            }), html`<option>${t`Loading...`}</option>`)}
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
