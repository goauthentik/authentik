import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { AccountSwitchStage, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-stage-account-switch-form")
export class AccountSwitchStageForm extends BaseStageForm<AccountSwitchStage> {
    loadInstance(pk: string): Promise<AccountSwitchStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesAccountSelectionSwitchRetrieve({
            stageUuid: pk,
        });
    }

    async send(data: AccountSwitchStage): Promise<AccountSwitchStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesAccountSelectionSwitchUpdate({
                stageUuid: this.instance.pk || "",
                accountSwitchStageRequest: data,
            });
        }
        return new StagesApi(DEFAULT_CONFIG).stagesAccountSelectionSwitchCreate({
            accountSwitchStageRequest: data,
        });
    }

    protected override renderForm(): TemplateResult {
        return html`<span>
                ${msg("Activate the account selected by an earlier Account Selection stage.")}
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
        "ak-stage-account-switch-form": AccountSwitchStageForm;
    }
}
