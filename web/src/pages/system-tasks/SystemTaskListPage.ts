import { t } from "@lingui/macro";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/SpinnerButton";
import "../../elements/buttons/ActionButton";
import { TableColumn } from "../../elements/table/Table";
import { AdminApi, Task, TaskStatusEnum } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";

@customElement("ak-system-task-list")
export class SystemTaskListPage extends TablePage<Task> {
    searchEnabled(): boolean {
        return false;
    }
    pageTitle(): string {
        return t`System Tasks`;
    }
    pageDescription(): string {
        return t`Long-running operations which authentik executes in the background.`;
    }
    pageIcon(): string {
        return "pf-icon pf-icon-automation";
    }

    @property()
    order = "slug";

    apiEndpoint(page: number): Promise<AKResponse<Task>> {
        return new AdminApi(DEFAULT_CONFIG).adminSystemTasksList().then((tasks) => {
            return {
                pagination: {
                    count: tasks.length,
                    totalPages: 1,
                    startIndex: 1,
                    endIndex: tasks.length,
                    current: page,
                },
                results: tasks,
            };
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Identifier`, t`task_name`),
            new TableColumn("Description"),
            new TableColumn("Last run"),
            new TableColumn("Status"),
            new TableColumn("Messages"),
            new TableColumn(""),
        ];
    }

    taskStatus(task: Task): TemplateResult {
        switch (task.status) {
            case TaskStatusEnum.Successful:
                return html`<i class="fas fa-check pf-m-success" > </i> ${t`Successful`}`;
            case TaskStatusEnum.Warning:
                return html`<i class="fas fa-exclamation-triangle pf-m-warning" > </i> ${t`Warning`}`;
            case TaskStatusEnum.Error:
                return html`<i class="fas fa-times pf-m-danger" > </i> ${t`Error`}`;
            default:
                return html`<i class="fas fa-question-circle" > </i> ${t`Unknown`}`;
        }
    }

    row(item: Task): TemplateResult[] {
        return [
            html`${item.taskName}`,
            html`${item.taskDescription}`,
            html`${item.taskFinishTimestamp.toLocaleString()}`,
            this.taskStatus(item),
            html`${item.messages.map(m => {
                return html`<li>${m}</li>`;
            })}`,
            html`<ak-action-button
                .apiRequest=${() => {
                    return new AdminApi(DEFAULT_CONFIG).adminSystemTasksRetry({
                        id: item.taskName
                    });
                }}>
                ${t`Retry Task`}
            </ak-action-button>`,
        ];
    }

}
