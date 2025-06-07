import "@goauthentik/admin/rbac/ObjectPermissionModal";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { getRelativeTime } from "@goauthentik/common/utils";
import { PFColor } from "@goauthentik/elements/Label";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/events/LogViewer";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import { PaginatedResponse, Table } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

import { Schedule, Task, TasksApi, TasksTasksListStateEnum } from "@goauthentik/api";

@customElement("ak-task-list")
export class TaskList extends Table<Task> {
    expandable = true;
    clearOnRefresh = true;

    @property()
    schedule: Schedule | undefined;

    searchEnabled(): boolean {
        return true;
    }

    @property()
    order = "-mtime";

    static get styles(): CSSResult[] {
        return super.styles.concat(PFDescriptionList);
    }

    async apiEndpoint(): Promise<PaginatedResponse<Task>> {
        const excludeScheduled = this.schedule === undefined;
        return new TasksApi(DEFAULT_CONFIG).tasksTasksList({
            ...(await this.defaultEndpointConfig()),
            excludeScheduled: excludeScheduled,
            scheduleUid: this.schedule?.uid,
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Task"), "actor_name"),
            new TableColumn(msg("Queue"), "queue_name"),
            new TableColumn(msg("Last updated"), "mtime"),
            new TableColumn(msg("State"), "state"),
            new TableColumn(msg("Actions")),
        ];
    }

    taskState(task: Task): TemplateResult {
        switch (task.state) {
            case TasksTasksListStateEnum.Queued:
                return html`<ak-label color=${PFColor.Grey}>${msg("Waiting to run")}</ak-label>`;
            case TasksTasksListStateEnum.Consumed:
                return html`<ak-label color=${PFColor.Blue}>${msg("Running")}</ak-label>`;
            case TasksTasksListStateEnum.Done:
                return html`<ak-label color=${PFColor.Green}>${msg("Successful")}</ak-label>`;
            case TasksTasksListStateEnum.Rejected:
                return html`<ak-label color=${PFColor.Red}>${msg("Error")}</ak-label>`;
            default:
                return html`<ak-label color=${PFColor.Grey}>${msg("Unknown")}</ak-label>`;
        }
    }

    row(item: Task): TemplateResult[] {
        return [
            html`<div>${item.actorName}</div>
                <small>${item.uid}</small>`,
            html`${item.queueName}`,
            html`<div>${getRelativeTime(item.mtime)}</div>
                <small>${item.mtime.toLocaleString()}</small>`,
            this.taskState(item),
            html``,
        ];
    }

    renderExpanded(item: Task): TemplateResult {
        return html` <td role="cell" colspan="3">
            <div class="pf-c-table__expandable-row-content">
                <div class="pf-c-content">
                    <ak-log-viewer .logs=${item?.messages}></ak-log-viewer>
                </div>
            </div>
        </td>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-task-list": TaskList;
    }
}
