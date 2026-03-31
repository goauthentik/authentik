import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { AKElement } from "#elements/Base";
import { PFColor } from "#elements/Label";

import { LastTaskStatusEnum, TaskAggregatedStatusEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";

@customElement("ak-task-status")
export class TaskStatus extends AKElement {
    public static styles: CSSResult[] = [PFButton];

    @property()
    status?: TaskAggregatedStatusEnum | TaskAggregatedStatusEnum | LastTaskStatusEnum;

    render(): TemplateResult {
        switch (this.status) {
            case TaskAggregatedStatusEnum.Queued:
            case LastTaskStatusEnum.Queued:
                return html`<ak-label color=${PFColor.Grey}>${msg("Waiting to run")}</ak-label>`;
            case TaskAggregatedStatusEnum.Consumed:
            case LastTaskStatusEnum.Consumed:
                return html`<ak-label color=${PFColor.Blue}>${msg("Consumed")}</ak-label>`;
            case TaskAggregatedStatusEnum.Preprocess:
            case LastTaskStatusEnum.Preprocess:
                return html`<ak-label color=${PFColor.Blue}>${msg("Pre-processing")}</ak-label>`;
            case TaskAggregatedStatusEnum.Running:
            case LastTaskStatusEnum.Running:
                return html`<ak-label color=${PFColor.Blue}>${msg("Running")}</ak-label>`;
            case TaskAggregatedStatusEnum.Postprocess:
            case LastTaskStatusEnum.Postprocess:
                return html`<ak-label color=${PFColor.Blue}>${msg("Post-processing")}</ak-label>`;
            case TaskAggregatedStatusEnum.Done:
            case LastTaskStatusEnum.Done:
            case TaskAggregatedStatusEnum.Info:
            case LastTaskStatusEnum.Info:
                return html`<ak-label color=${PFColor.Green}>${msg("Successful")}</ak-label>`;
            case TaskAggregatedStatusEnum.Warning:
            case LastTaskStatusEnum.Warning:
                return html`<ak-label color=${PFColor.Orange}>${msg("Warning")}</ak-label>`;
            case TaskAggregatedStatusEnum.Rejected:
            case LastTaskStatusEnum.Rejected:
            case TaskAggregatedStatusEnum.Error:
            case LastTaskStatusEnum.Error:
                return html`<ak-label color=${PFColor.Red}>${msg("Error")}</ak-label>`;
            default:
                return html`<ak-label color=${PFColor.Grey}>${msg("Unknown")}</ak-label>`;
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-task-status": TaskStatus;
    }
}
