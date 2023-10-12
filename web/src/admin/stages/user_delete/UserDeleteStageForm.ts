import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { StagesApi, UserDeleteStage } from "@goauthentik/api";

@customElement("ak-stage-user-delete-form")
export class UserDeleteStageForm extends ModelForm<UserDeleteStage, string> {
    loadInstance(pk: string): Promise<UserDeleteStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesUserDeleteRetrieve({
            stageUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated stage.");
        } else {
            return msg("Successfully created stage.");
        }
    }

    async send(data: UserDeleteStage): Promise<UserDeleteStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesUserDeleteUpdate({
                stageUuid: this.instance.pk || "",
                userDeleteStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesUserDeleteCreate({
                userDeleteStageRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html` <span>
                ${msg(
                    "Delete the currently pending user. CAUTION, this stage does not ask for confirmation. Use a consent stage to ensure the user is aware of their actions.",
                )}
            </span>
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>`;
    }
}
