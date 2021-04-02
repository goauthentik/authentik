import { FlowDesignationEnum, FlowsApi, IdentificationStage, IdentificationStageUserFieldsEnum, StagesApi } from "authentik-api";
import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { Form } from "../../../elements/forms/Form";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";
import "../../../elements/forms/FormGroup";
import { until } from "lit-html/directives/until";

@customElement("ak-stage-identification-form")
export class IdentificationStageForm extends Form<IdentificationStage> {

    set stageUUID(value: string) {
        new StagesApi(DEFAULT_CONFIG).stagesIdentificationRead({
            stageUuid: value,
        }).then(stage => {
            this.stage = stage;
        });
    }

    @property({attribute: false})
    stage?: IdentificationStage;

    getSuccessMessage(): string {
        if (this.stage) {
            return gettext("Successfully updated stage.");
        } else {
            return gettext("Successfully created stage.");
        }
    }

    send = (data: IdentificationStage): Promise<IdentificationStage> => {
        if (this.stage) {
            return new StagesApi(DEFAULT_CONFIG).stagesIdentificationUpdate({
                stageUuid: this.stage.pk || "",
                data: data
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesIdentificationCreate({
                data: data
            });
        }
    };

    isUserFieldSelected(field: IdentificationStageUserFieldsEnum): boolean {
        return (this.stage?.userFields || []).filter(isField => {
            return field === isField;
        }).length > 0;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${gettext("Name")}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.stage?.name || "")}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header">
                    ${gettext("Stage-specific settings")}
                </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${gettext("User fields")}
                        ?required=${true}
                        name="transports">
                        <select name="users" class="pf-c-form-control" multiple>
                            <option value=${IdentificationStageUserFieldsEnum.Username} ?selected=${this.isUserFieldSelected(IdentificationStageUserFieldsEnum.Username)}>
                                ${IdentificationStageUserFieldsEnum.Username}
                            </option>
                            <option value=${IdentificationStageUserFieldsEnum.Email} ?selected=${this.isUserFieldSelected(IdentificationStageUserFieldsEnum.Email)}>
                                ${IdentificationStageUserFieldsEnum.Email}
                            </option>
                        </select>
                        <p class="pf-c-form__helper-text">${gettext("Fields a user can identify themselves with.")}</p>
                        <p class="pf-c-form__helper-text">${gettext("Hold control/command to select multiple items.")}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="caseInsensitiveMatching">
                        <div class="pf-c-check">
                            <input type="checkbox" class="pf-c-check__input" ?checked=${this.stage?.caseInsensitiveMatching || true}>
                            <label class="pf-c-check__label">
                                ${gettext("Case insensitive matching")}
                            </label>
                        </div>
                        <p class="pf-c-form__helper-text">${gettext("When enabled, user fields are matched regardless of their casing.")}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="showMatchedUser">
                        <div class="pf-c-check">
                            <input type="checkbox" class="pf-c-check__input" ?checked=${this.stage?.showMatchedUser || true}>
                            <label class="pf-c-check__label">
                                ${gettext("Show matched user")}
                            </label>
                        </div>
                        <p class="pf-c-form__helper-text">${gettext("When a valid username/email has been entered, and this option is enabled, the user's username and avatar will be shown. Otherwise, the text that the user entered will be shown.")}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${gettext("Enrollment flow")}
                        name="enrollmentFlow">
                        <select class="pf-c-form-control">
                            <option value="" ?selected=${this.stage?.enrollmentFlow === undefined}>---------</option>
                            ${until(new FlowsApi(DEFAULT_CONFIG).flowsInstancesList({
                                ordering: "pk",
                                designation: FlowDesignationEnum.Enrollment,
                            }).then(flows => {
                                return flows.results.map(flow => {
                                    let selected = this.stage?.enrollmentFlow === flow.pk;
                                    return html`<option value=${ifDefined(flow.pk)} ?selected=${selected}>${flow.name} (${flow.slug})</option>`;
                                });
                            }))}
                        </select>
                        <p class="pf-c-form__helper-text">${gettext("Optional enrollment flow, which is linked at the bottom of the page.")}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${gettext("Recovery flow")}
                        name="recoveryFlow">
                        <select class="pf-c-form-control">
                            <option value="" ?selected=${this.stage?.recoveryFlow === undefined}>---------</option>
                            ${until(new FlowsApi(DEFAULT_CONFIG).flowsInstancesList({
                                ordering: "pk",
                                designation: FlowDesignationEnum.Recovery,
                            }).then(flows => {
                                return flows.results.map(flow => {
                                    let selected = this.stage?.recoveryFlow === flow.pk;
                                    return html`<option value=${ifDefined(flow.pk)} ?selected=${selected}>${flow.name} (${flow.slug})</option>`;
                                });
                            }))}
                        </select>
                        <p class="pf-c-form__helper-text">${gettext("Optional recovery flow, which is linked at the bottom of the page.")}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }

}
