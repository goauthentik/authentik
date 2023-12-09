import { BaseStageForm } from "@goauthentik/admin/stages/BaseStageForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { DenyStage, StagesApi } from "@goauthentik/api";

@customElement("ak-stage-deny-form")
export class DenyStageForm extends BaseStageForm<DenyStage> {
    loadInstance(pk: string): Promise<DenyStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesDenyRetrieve({
            stageUuid: pk,
        });
    }

    async send(data: DenyStage): Promise<DenyStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesDenyUpdate({
                stageUuid: this.instance.pk || "",
                denyStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesDenyCreate({
                denyStageRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`
            <span>
                ${msg(
                    "Statically deny the flow. To use this stage effectively, disable *Evaluate when flow is planned* on the respective binding.",
                )}
            </span>
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Stage-specific settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("Deny message")} name="denyMessage">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.denyMessage || "")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Message shown when this stage is run.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        `;
    }
}
