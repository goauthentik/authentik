import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { DummyStage, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-stage-dummy-form")
export class DummyStageForm extends BaseStageForm<DummyStage> {
    protected endpoints = {
        load: (stageUuid: string) => aki(StagesApi).stagesDummyRetrieve({ stageUuid }),
        create: (dummyStageRequest: DummyStage) =>
            aki(StagesApi).stagesDummyCreate({ dummyStageRequest }),
        update: (stageUuid: string, dummyStageRequest: DummyStage) =>
            aki(StagesApi).stagesDummyUpdate({ stageUuid, dummyStageRequest }),
    };

    protected override renderForm(): TemplateResult {
        return html` <span>
                ${msg(
                    "Dummy stage used for testing. Shows a simple continue button and always passes.",
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
            <ak-switch-input
                name="throwError"
                label=${msg("Throw error?")}
                ?checked=${this.instance?.throwError ?? false}
            ></ak-switch-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-dummy-form": DummyStageForm;
    }
}
