import "#components/ak-text-input";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { AccountSwitchStage, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-stage-account-switch-form")
export class AccountSwitchStageForm extends BaseStageForm<AccountSwitchStage> {
    protected override loadInstance(pk: string): Promise<AccountSwitchStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesAccountSelectionSwitchRetrieve({
            stageUuid: pk,
        });
    }

    protected override async send(data: AccountSwitchStage): Promise<AccountSwitchStage> {
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
        "ak-stage-account-switch-form": AccountSwitchStageForm;
    }
}
