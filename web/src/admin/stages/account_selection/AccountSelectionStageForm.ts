import "#components/ak-text-input";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { AccountSelectionStage, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-stage-account-selection-form")
export class AccountSelectionStageForm extends BaseStageForm<AccountSelectionStage> {
    protected override loadInstance(pk: string): Promise<AccountSelectionStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesAccountSelectionSelectionRetrieve({
            stageUuid: pk,
        });
    }

    protected override async send(data: AccountSelectionStage): Promise<AccountSelectionStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesAccountSelectionSelectionUpdate({
                stageUuid: this.instance.pk || "",
                accountSelectionStageRequest: data,
            });
        }
        return new StagesApi(DEFAULT_CONFIG).stagesAccountSelectionSelectionCreate({
            accountSelectionStageRequest: data,
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
        "ak-stage-account-selection-form": AccountSelectionStageForm;
    }
}
