import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { DenyStage, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

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
        }
        return new StagesApi(DEFAULT_CONFIG).stagesDenyCreate({
            denyStageRequest: data,
        });
    }

    renderForm(): TemplateResult {
        return html`
            <span>
                ${msg(
                    "Statically deny the flow. To use this stage effectively, disable *Evaluate when flow is planned* on the respective binding.",
                )}
            </span>
            <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group open label="${msg("Stage-specific settings")}">
                <div class="pf-c-form">
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

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-deny-form": DenyStageForm;
    }
}
