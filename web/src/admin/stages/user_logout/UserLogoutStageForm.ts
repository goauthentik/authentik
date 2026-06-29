import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { StagesApi, UserLogoutStage } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-stage-user-logout-form")
export class UserLogoutStageForm extends BaseStageForm<UserLogoutStage> {
    loadInstance(pk: string): Promise<UserLogoutStage> {
        return aki(StagesApi).stagesUserLogoutRetrieve({
            stageUuid: pk,
        });
    }

    async send(data: UserLogoutStage): Promise<UserLogoutStage> {
        if (this.instance) {
            return aki(StagesApi).stagesUserLogoutUpdate({
                stageUuid: this.instance.pk || "",
                userLogoutStageRequest: data,
            });
        }
        return aki(StagesApi).stagesUserLogoutCreate({
            userLogoutStageRequest: data,
        });
    }

    protected override renderForm(): TemplateResult {
        return html` <span>${msg("Remove the user from the current session.")}</span>
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
        "ak-stage-user-logout-form": UserLogoutStageForm;
    }
}
