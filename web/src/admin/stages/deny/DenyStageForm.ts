import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { DenyStage, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-stage-deny-form")
export class DenyStageForm extends BaseStageForm<DenyStage> {
    protected endpoints = {
        load: (stageUuid: string) => aki(StagesApi).stagesDenyRetrieve({ stageUuid }),
        create: (denyStageRequest: DenyStage) =>
            aki(StagesApi).stagesDenyCreate({ denyStageRequest }),
        update: (stageUuid: string, denyStageRequest: DenyStage) =>
            aki(StagesApi).stagesDenyUpdate({ stageUuid, denyStageRequest }),
    };

    protected override renderForm(): TemplateResult {
        return html`
            <span>
                ${msg(
                    "Statically deny the flow. To use this stage effectively, disable *Evaluate when flow is planned* on the respective binding.",
                )}
            </span>
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
            ></ak-text-input>
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
