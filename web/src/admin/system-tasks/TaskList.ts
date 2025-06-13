import { formatElapsedTime } from "#common/temporal";
import "@goauthentik/admin/rbac/ObjectPermissionModal";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
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

import { Task, TasksApi, TasksTasksListStateEnum } from "@goauthentik/api";

@customElement("ak-task-list")
export class TaskList extends Table<Task> {
    expandable = true;
    clearOnRefresh = true;

    @property()
    relObjAppLabel?: string;
    @property()
    relObjModel?: string;
    @property()
    relObjId?: string;

    @property()
    showOnlyStandalone: boolean = true;

    searchEnabled(): boolean {
        return true;
    }

    @property()
    order = "-mtime";

    static get styles(): CSSResult[] {
        return super.styles.concat(PFDescriptionList);
    }

    async apiEndpoint(): Promise<PaginatedResponse<Task>> {
        const relObjIdIsnull =
            typeof this.relObjId !== "undefined"
                ? undefined
                : this.showOnlyStandalone
                  ? true
                  : undefined;
        return new TasksApi(DEFAULT_CONFIG).tasksTasksList({
            ...(await this.defaultEndpointConfig()),
            relObjContentTypeAppLabel: this.relObjAppLabel,
            relObjContentTypeModel: this.relObjModel,
            relObjId: this.relObjId,
            relObjIdIsnull,
        });
    }

    #toggleShowOnlyStandalone = () => {
        this.showOnlyStandalone = !this.showOnlyStandalone;
        this.page = 1;
        return this.fetch();
    };

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Task"), "actor_name"),
            new TableColumn(msg("Queue"), "queue_name"),
            new TableColumn(msg("Last updated"), "mtime"),
            new TableColumn(msg("State"), "state"),
            new TableColumn(msg("Actions")),
        ];
    }

    renderToolbarAfter(): TemplateResult {
        console.log("task show standalone");
        console.log(this.showOnlyStandalone);
        if (this.relObjId !== undefined) {
            return html``;
        }
        return html`&nbsp;
            <div class="pf-c-toolbar__group pf-m-filter-group">
                <div class="pf-c-toolbar__item pf-m-search-filter">
                    <div class="pf-c-input-group">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${this.showOnlyStandalone}
                                @change=${this.#toggleShowOnlyStandalone}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria - hidden="true"> </i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">
                                ${msg("Show only standalone tasks")}
                            </span>
                        </label>
                    </div>
                </div>
            </div>`;
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
                <small>${item.uid.replace(new RegExp("^authentik."), "")}</small>`,
            html`${item.queueName}`,
            html`<div>${formatElapsedTime(item.mtime || new Date())}</div>
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
