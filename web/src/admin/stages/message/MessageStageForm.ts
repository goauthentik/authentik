import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { MessageStage, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-stage-message-form")
export class MessageStageForm extends BaseStageForm<MessageStage> {
    protected endpoints = {
        load: (stageUuid: string) => aki(StagesApi).stagesMessageRetrieve({ stageUuid }),
        create: (messageStageRequest: MessageStage) =>
            aki(StagesApi).stagesMessageCreate({ messageStageRequest }),
        update: (stageUuid: string, messageStageRequest: MessageStage) =>
            aki(StagesApi).stagesMessageUpdate({ stageUuid, messageStageRequest }),
    };

    protected override renderForm(): TemplateResult {
        return html`<span>
                ${msg("Present an informational message to the user.", {
                    id: "message-stage.description",
                })}
            </span>
            <ak-form-element-horizontal
                label=${msg("Name", { id: "message-stage.name.label" })}
                required
                name="name"
            >
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Title", { id: "message-stage.title.label" })}
                name="title"
            >
                <input
                    type="text"
                    value="${ifDefined(this.instance?.title || "")}"
                    class="pf-c-form-control"
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Message", { id: "message-stage.message.label" })}
                required
                name="message"
            >
                <textarea
                    class="pf-c-form-control pf-m-monospace"
                    rows="8"
                    style="min-height: 16rem; max-height: 50vh; resize: none;"
                    .value=${this.instance?.message ?? ""}
                    required
                ></textarea>
                <p class="pf-c-form__helper-text">
                    ${msg("The message to be displayed to the user. Basic HTML is supported.", {
                        id: "message-stage.message.description",
                    })}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Button Text", { id: "message-stage.button-text.label" })}
                name="buttonText"
            >
                <input
                    type="text"
                    value="${ifDefined(this.instance?.buttonText || "")}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "The text to be displayed on the acknowledgment button. If left blank, this will show 'Continue'.",
                        { id: "message-stage.button-text.description" },
                    )}
                </p>
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-message-form": MessageStageForm;
    }
}
