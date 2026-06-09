import "#components/ak-text-input";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { StagesApi, UserSelectionStage } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-stage-user-selection-form")
export class UserSelectionStageForm extends BaseStageForm<UserSelectionStage> {
    protected override loadInstance(pk: string): Promise<UserSelectionStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesUserSelectionSelectionRetrieve({
            stageUuid: pk,
        });
    }

    protected override async send(data: UserSelectionStage): Promise<UserSelectionStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesUserSelectionSelectionUpdate({
                stageUuid: this.instance.pk || "",
                userSelectionStageRequest: data,
            });
        }
        return new StagesApi(DEFAULT_CONFIG).stagesUserSelectionSelectionCreate({
            userSelectionStageRequest: data,
        });
    }

    protected override renderForm(): TemplateResult {
        return html`<span> ${msg("Prompt the user to select a browser-local account.")} </span>
            <ak-text-input
                label=${msg("Name")}
                required
                name="name"
                value="${ifDefined(this.instance?.name || "")}"
            ></ak-text-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-user-selection-form": UserSelectionStageForm;
    }
}
