import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { StagesApi, UserDeleteStage } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-stage-user-delete-form")
export class UserDeleteStageForm extends BaseStageForm<UserDeleteStage> {
    loadInstance(pk: string): Promise<UserDeleteStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesUserDeleteRetrieve({
            stageUuid: pk,
        });
    }

    async send(data: UserDeleteStage): Promise<UserDeleteStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesUserDeleteUpdate({
                stageUuid: this.instance.pk || "",
                userDeleteStageRequest: data,
            });
        }
        return new StagesApi(DEFAULT_CONFIG).stagesUserDeleteCreate({
            userDeleteStageRequest: data,
        });
    }

    protected override renderForm(): TemplateResult {
        return html` <span>
                ${msg(
                    "Delete the currently pending user. CAUTION, this stage does not ask for confirmation. Use a consent stage to ensure the user is aware of their actions.",
                )}
            </span>
            <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-user-delete-form": UserDeleteStageForm;
    }
}
