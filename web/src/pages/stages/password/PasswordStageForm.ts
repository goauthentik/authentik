import { FlowDesignationEnum, FlowsApi, PasswordStage, PasswordStageBackendsEnum, StagesApi } from "authentik-api";
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

@customElement("ak-stage-password-form")
export class PasswordStageForm extends Form<PasswordStage> {

    set stageUUID(value: string) {
        new StagesApi(DEFAULT_CONFIG).stagesPasswordRead({
            stageUuid: value,
        }).then(stage => {
            this.stage = stage;
        });
    }

    @property({attribute: false})
    stage?: PasswordStage;

    getSuccessMessage(): string {
        if (this.stage) {
            return t`Successfully updated stage.`;
        } else {
            return t`Successfully created stage.`;
        }
    }

    send = (data: PasswordStage): Promise<PasswordStage> => {
        if (this.stage) {
            return new StagesApi(DEFAULT_CONFIG).stagesPasswordUpdate({
                stageUuid: this.stage.pk || "",
                data: data
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesPasswordCreate({
                data: data
            });
        }
    };

    isBackendSelected(field: PasswordStageBackendsEnum): boolean {
        return (this.stage?.backends || []).filter(isField => {
            return field === isField;
        }).length > 0;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`Validate the user's password against the selected backend(s).`}
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
                        label=${t`Backends`}
                        ?required=${true}
                        name="backends">
                        <select name="users" class="pf-c-form-control" multiple>
                            <option value=${PasswordStageBackendsEnum.DjangoContribAuthBackendsModelBackend} ?selected=${this.isBackendSelected(PasswordStageBackendsEnum.DjangoContribAuthBackendsModelBackend)}>
                                ${t`authentik Builtin Database`}
                                </option>
                            <option value=${PasswordStageBackendsEnum.AuthentikSourcesLdapAuthLdapBackend} ?selected=${this.isBackendSelected(PasswordStageBackendsEnum.AuthentikSourcesLdapAuthLdapBackend)}>
                                ${t`authentik LDAP Backend`}
                            </option>
                        </select>
                        <p class="pf-c-form__helper-text">${t`Selection of backends to test the password against.`}</p>
                        <p class="pf-c-form__helper-text">${t`Hold control/command to select multiple items.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Configuration flow`}
                        ?required=${true}
                        name="configureFlow">
                        <select class="pf-c-form-control">
                            <option value="" ?selected=${this.stage?.configureFlow === undefined}>---------</option>
                            ${until(new FlowsApi(DEFAULT_CONFIG).flowsInstancesList({
                                ordering: "pk",
                                designation: FlowDesignationEnum.StageConfiguration,
                            }).then(flows => {
                                return flows.results.map(flow => {
                                    let selected = this.stage?.configureFlow === flow.pk;
                                    if (!this.stage?.pk && !this.stage?.configureFlow && flow.slug === "default-password-change") {
                                        selected = true;
                                    }
                                    return html`<option value=${ifDefined(flow.pk)} ?selected=${selected}>${flow.name} (${flow.slug})</option>`;
                                });
                            }), html`<option>${t`Loading...`}</option>`)}
                        </select>
                        <p class="pf-c-form__helper-text">${t`Flow used by an authenticated user to configure their password. If empty, user will not be able to configure change their password.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Failed attempts before cancel`}
                        ?required=${true}
                        name="failedAttemptsBeforeCancel">
                        <input type="number" value="${first(this.stage?.failedAttemptsBeforeCancel, 5)}" class="pf-c-form-control" required>
                        <p class="pf-c-form__helper-text">${t`How many attempts a user has before the flow is canceled. To lock the user out, use a reputation policy and a user_write stage.`}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }

}
