import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { StagesApi, UserLogoutStage } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-stage-user-logout-form")
export class UserLogoutStageForm extends BaseStageForm<UserLogoutStage> {
    protected endpoints = {
        load: (stageUuid: string) => aki(StagesApi).stagesUserLogoutRetrieve({ stageUuid }),
        create: (userLogoutStageRequest: UserLogoutStage) =>
            aki(StagesApi).stagesUserLogoutCreate({ userLogoutStageRequest }),
        update: (stageUuid: string, userLogoutStageRequest: UserLogoutStage) =>
            aki(StagesApi).stagesUserLogoutUpdate({ stageUuid, userLogoutStageRequest }),
    };

    protected override renderForm(): TemplateResult {
        return html` <span>${msg("Remove the user from the current session.")}</span>
            <ak-text-input
                label=${msg("Stage Name", {
                    id: "stage.name.label",
                })}
                required
                name="name"
                value=${this.instance?.name || ""}
                placeholder=${msg("Type a name for this stage...", {
                    id: "stage.name.placeholder",
                })}
                ?autofocus=${!this.instance}
            ></ak-text-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-user-logout-form": UserLogoutStageForm;
    }
}
