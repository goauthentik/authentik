import "#components/ak-text-input";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import { aki } from "#common/api/client";
import { APIMessage, MessageLevel } from "#common/messages";

import { renderModal } from "#elements/dialogs";
import { AKFormSubmittedEvent } from "#elements/forms/events";
import { ModelForm } from "#elements/forms/ModelForm";
import { SlottedTemplateResult } from "#elements/types";
import { StrictUnsafe } from "#elements/utils/unsafe";

import { Stage, StageDuplicateRequest, StagesApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

/**
 * Asks for the name of a copy of {@linkcode instance}, and creates it.
 */
@customElement("ak-stage-duplicate-form")
export class StageDuplicateForm extends ModelForm<Stage, string, StageDuplicateRequest> {
    protected override send(data: StageDuplicateRequest): Promise<Stage> {
        if (!this.instance) {
            return Promise.reject(new Error("No stage to duplicate"));
        }

        return aki(StagesApi).stagesAllDuplicateCreate({
            stageUuid: this.instance.pk,
            stageDuplicateRequest: data,
        });
    }

    protected override formatHeadline(): string {
        return msg("Duplicate Stage", { id: "stage.duplicate.headline" });
    }

    protected override formatSubmitLabel(): string {
        return msg("Duplicate", { id: "common.actions.duplicate" });
    }

    protected override formatSubmittingLabel(): string {
        return msg("Duplicating stage...", { id: "stage.duplicate.pending" });
    }

    protected override formatSubmittedLabel(): string {
        return msg("Stage duplicated", { id: "stage.duplicate.success" });
    }

    protected override formatAPISuccessMessage(): APIMessage {
        return { level: MessageLevel.success, message: this.formatSubmittedLabel() };
    }

    protected override renderForm(): SlottedTemplateResult {
        const name = this.instance?.name ?? "";

        return html`<p class="pf-c-form__helper-text">
                ${msg(
                    str`The copy keeps the settings of ${name} and refers to the same objects, such as prompts, sources, and flows. It is not bound to any flow. Secrets, such as passwords and API keys, are only copied if you can edit ${name}.`,
                    { id: "stage.duplicate.description" },
                )}
            </p>
            <ak-text-input
                label=${msg("Stage Name", { id: "stage.name.label" })}
                required
                name=${this.field("name")}
                value=${msg(str`${name} (copy)`, { id: "stage.duplicate.name.default-value" })}
                placeholder=${msg("Type a name for this stage...", {
                    id: "stage.name.placeholder",
                })}
                autofocus
            ></ak-text-input>`;
    }
}

/**
 * Ask for a name for a copy of the stage, create it, and open the copy for editing.
 *
 * @param invokerElement The element that opened the modal. A table containing it refreshes
 *   after each modal is submitted.
 *
 * @returns A promise that resolves when the last modal is closed.
 */
export async function showStageDuplicateModal(
    stage: Stage,
    invokerElement?: HTMLElement,
): Promise<void> {
    const form = new StageDuplicateForm();
    form.instance = stage;

    let copy = null as Stage | null;

    form.addEventListener(AKFormSubmittedEvent.eventName, (event) => {
        copy = (event as AKFormSubmittedEvent<Stage>).response;
    });

    await renderModal(form, { invokerElement });

    if (!copy) {
        return;
    }

    // The same form the copy's edit button opens.
    await renderModal(
        StrictUnsafe<ModelForm<Stage, string>>(copy.component, { instancePk: copy.pk }),
        { invokerElement },
    );
}

export function StageDuplicateButton(stage: Stage): SlottedTemplateResult {
    const label = msg("Duplicate", { id: "common.actions.duplicate" });

    return html`<button
        type="button"
        class="pf-c-button pf-m-plain"
        aria-label=${msg(str`Duplicate "${stage.name}"`, { id: "stage.duplicate.aria-label" })}
        @click=${(event: Event) =>
            showStageDuplicateModal(stage, event.currentTarget as HTMLElement)}
    >
        <pf-tooltip position="top" content=${label}>
            <i class="fas fa-copy" aria-hidden="true"></i>
        </pf-tooltip>
    </button>`;
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-duplicate-form": StageDuplicateForm;
    }
}
