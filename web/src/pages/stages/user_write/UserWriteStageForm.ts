import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import { CoreApi, StagesApi, UserWriteStage } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../../api/Config";
import "../../../elements/forms/FormGroup";
import "../../../elements/forms/HorizontalFormElement";
import { ModelForm } from "../../../elements/forms/ModelForm";
import { first } from "../../../utils";

@customElement("ak-stage-user-write-form")
export class UserWriteStageForm extends ModelForm<UserWriteStage, string> {
    loadInstance(pk: string): Promise<UserWriteStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesUserWriteRetrieve({
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

    send = (data: UserWriteStage): Promise<UserWriteStage> => {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesUserWriteUpdate({
                stageUuid: this.instance.pk || "",
                userWriteStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesUserWriteCreate({
                userWriteStageRequest: data,
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`Write any data from the flow's context's 'prompt_data' to the currently pending user. If no user
                is pending, a new user is created, and data is written to them.`}
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
                    <ak-form-element-horizontal name="createUsersAsInactive">
                        <div class="pf-c-check">
                            <input
                                type="checkbox"
                                class="pf-c-check__input"
                                ?checked=${first(this.instance?.createUsersAsInactive, true)}
                            />
                            <label class="pf-c-check__label">
                                ${t`Create users as inactive`}
                            </label>
                        </div>
                        <p class="pf-c-form__helper-text">
                            ${t`Mark newly created users as inactive.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`Group`} name="createUsersGroup">
                        <select class="pf-c-form-control">
                            <option
                                value=""
                                ?selected=${this.instance?.createUsersGroup === undefined}
                            >
                                ---------
                            </option>
                            ${until(
                                new CoreApi(DEFAULT_CONFIG).coreGroupsList({}).then((groups) => {
                                    return groups.results.map((group) => {
                                        return html`<option
                                            value=${ifDefined(group.pk)}
                                            ?selected=${this.instance?.createUsersGroup ===
                                            group.pk}
                                        >
                                            ${group.name}
                                        </option>`;
                                    });
                                }),
                                html`<option>${t`Loading...`}</option>`,
                            )}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${t`Newly created users are added to this group, if a group is selected.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
