import { FlowDesignationEnum, FlowsApi, IdentificationStage, IdentificationStageUserFieldsEnum, StagesApi } from "authentik-api";
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

@customElement("ak-stage-identification-form")
export class IdentificationStageForm extends ModelForm<IdentificationStage, string> {

    loadInstance(pk: string): Promise<IdentificationStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesIdentificationRetrieve({
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

    send = (data: IdentificationStage): Promise<IdentificationStage> => {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesIdentificationUpdate({
                stageUuid: this.instance.pk || "",
                data: data
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesIdentificationCreate({
                data: data
            });
        }
    };

    isUserFieldSelected(field: IdentificationStageUserFieldsEnum): boolean {
        return (this.instance?.userFields || []).filter(isField => {
            return field === isField;
        }).length > 0;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`Let the user identify themselves with their username or Email address.`}
            </div>
            <ak-form-element-horizontal
                label=${t`Name`}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.instance?.name || "")}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header">
                    ${t`Stage-specific settings`}
                </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`User fields`}
                        name="userFields">
                        <select name="users" class="pf-c-form-control" multiple>
                            <option value=${IdentificationStageUserFieldsEnum.Username} ?selected=${this.isUserFieldSelected(IdentificationStageUserFieldsEnum.Username)}>
                                ${t`Username`}
                            </option>
                            <option value=${IdentificationStageUserFieldsEnum.Email} ?selected=${this.isUserFieldSelected(IdentificationStageUserFieldsEnum.Email)}>
                                ${t`Email`}
                            </option>
                        </select>
                        <p class="pf-c-form__helper-text">${t`Fields a user can identify themselves with. If no fields are selected, the user will only be able to use sources.`}</p>
                        <p class="pf-c-form__helper-text">${t`Hold control/command to select multiple items.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="caseInsensitiveMatching">
                        <div class="pf-c-check">
                            <input type="checkbox" class="pf-c-check__input" ?checked=${first(this.instance?.caseInsensitiveMatching, true)}>
                            <label class="pf-c-check__label">
                                ${t`Case insensitive matching`}
                            </label>
                        </div>
                        <p class="pf-c-form__helper-text">${t`When enabled, user fields are matched regardless of their casing.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="showMatchedUser">
                        <div class="pf-c-check">
                            <input type="checkbox" class="pf-c-check__input" ?checked=${first(this.instance?.showMatchedUser, true)}>
                            <label class="pf-c-check__label">
                                ${t`Show matched user`}
                            </label>
                        </div>
                        <p class="pf-c-form__helper-text">${t`When a valid username/email has been entered, and this option is enabled, the user's username and avatar will be shown. Otherwise, the text that the user entered will be shown.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Enrollment flow`}
                        name="enrollmentFlow">
                        <select class="pf-c-form-control">
                            <option value="" ?selected=${this.instance?.enrollmentFlow === undefined}>---------</option>
                            ${until(new FlowsApi(DEFAULT_CONFIG).flowsInstancesList({
                                ordering: "pk",
                                designation: FlowDesignationEnum.Enrollment,
                            }).then(flows => {
                                return flows.results.map(flow => {
                                    const selected = this.instance?.enrollmentFlow === flow.pk;
                                    return html`<option value=${ifDefined(flow.pk)} ?selected=${selected}>${flow.name} (${flow.slug})</option>`;
                                });
                            }), html`<option>${t`Loading...`}</option>`)}
                        </select>
                        <p class="pf-c-form__helper-text">${t`Optional enrollment flow, which is linked at the bottom of the page.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Recovery flow`}
                        name="recoveryFlow">
                        <select class="pf-c-form-control">
                            <option value="" ?selected=${this.instance?.recoveryFlow === undefined}>---------</option>
                            ${until(new FlowsApi(DEFAULT_CONFIG).flowsInstancesList({
                                ordering: "pk",
                                designation: FlowDesignationEnum.Recovery,
                            }).then(flows => {
                                return flows.results.map(flow => {
                                    const selected = this.instance?.recoveryFlow === flow.pk;
                                    return html`<option value=${ifDefined(flow.pk)} ?selected=${selected}>${flow.name} (${flow.slug})</option>`;
                                });
                            }), html`<option>${t`Loading...`}</option>`)}
                        </select>
                        <p class="pf-c-form__helper-text">${t`Optional recovery flow, which is linked at the bottom of the page.`}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }

}
