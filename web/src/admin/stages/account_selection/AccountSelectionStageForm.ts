import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { AccountSelectionStage, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-stage-account-selection-form")
export class AccountSelectionStageForm extends BaseStageForm<AccountSelectionStage> {
    loadInstance(pk: string): Promise<AccountSelectionStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesAccountSelectionSelectionRetrieve({
            stageUuid: pk,
        });
    }

    async send(data: AccountSelectionStage): Promise<AccountSelectionStage> {
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
        "ak-stage-account-selection-form": AccountSelectionStageForm;
    }
}
