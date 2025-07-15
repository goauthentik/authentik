import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { AKElement } from "#elements/Base";
import { PFColor } from "#elements/Label";

import {
    LastTaskStatusEnum,
    TaskAggregatedStatusEnum,
    TasksTasksListAggregatedStatusEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-task-status")
export class TaskStatus extends AKElement {
    @property()
    status?: TaskAggregatedStatusEnum | TasksTasksListAggregatedStatusEnum | LastTaskStatusEnum;

    static get styles(): CSSResult[] {
        return [PFBase, PFButton];
    }

    render(): TemplateResult {
        switch (this.status) {
            case TasksTasksListAggregatedStatusEnum.Queued:
            case TaskAggregatedStatusEnum.Queued:
            case LastTaskStatusEnum.Queued:
                return html`<ak-label color=${PFColor.Grey}>${msg("Waiting to run")}</ak-label>`;
            case TasksTasksListAggregatedStatusEnum.Consumed:
            case TaskAggregatedStatusEnum.Consumed:
            case LastTaskStatusEnum.Consumed:
                return html`<ak-label color=${PFColor.Blue}>${msg("Running")}</ak-label>`;
            case TasksTasksListAggregatedStatusEnum.Done:
            case TaskAggregatedStatusEnum.Done:
            case LastTaskStatusEnum.Done:
            case TasksTasksListAggregatedStatusEnum.Info:
            case TaskAggregatedStatusEnum.Info:
            case LastTaskStatusEnum.Info:
                return html`<ak-label color=${PFColor.Green}>${msg("Successful")}</ak-label>`;
            case TasksTasksListAggregatedStatusEnum.Warning:
            case TaskAggregatedStatusEnum.Warning:
            case LastTaskStatusEnum.Warning:
                return html`<ak-label color=${PFColor.Orange}>${msg("Warning")}</ak-label>`;
            case TasksTasksListAggregatedStatusEnum.Rejected:
            case TaskAggregatedStatusEnum.Rejected:
            case LastTaskStatusEnum.Rejected:
            case TasksTasksListAggregatedStatusEnum.Error:
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
