import {
    FlowsApi,
    AuthenticatorDuoStage,
    StagesApi,
    FlowsInstancesListDesignationEnum,
    AuthenticatorDuoStageRequest,
} from "authentik-api";
import { t } from "@lingui/macro";
import { customElement } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";
import "../../../elements/forms/FormGroup";
import { until } from "lit-html/directives/until";
import { first } from "../../../utils";
import { ModelForm } from "../../../elements/forms/ModelForm";

@customElement("ak-stage-authenticator-duo-form")
export class AuthenticatorDuoStageForm extends ModelForm<AuthenticatorDuoStage, string> {
    loadInstance(pk: string): Promise<AuthenticatorDuoStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorDuoRetrieve({
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

    send = (data: AuthenticatorDuoStage): Promise<AuthenticatorDuoStage> => {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorDuoPartialUpdate({
                stageUuid: this.instance.pk || "",
                patchedAuthenticatorDuoStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorDuoCreate({
                authenticatorDuoStageRequest: data as unknown as AuthenticatorDuoStageRequest,
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`Stage used to configure a duo-based authenticator. This stage should be used for configuration flows.`}
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
                        label=${t`Integration key`}
                        ?required=${true}
                        name="clientId"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.clientId, "")}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Secret key`}
                        ?required=${true}
                        ?writeOnly=${this.instance !== undefined}
                        name="clientSecret"
                    >
                        <input type="text" value="" class="pf-c-form-control" required />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`API Hostname`}
                        ?required=${true}
                        name="apiHostname"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.apiHostname, "")}"
                            class="pf-c-form-control"
                            required
                        />
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
