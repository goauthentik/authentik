import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import "../../elements/buttons/ActionButton";
import { TableColumn } from "../../elements/table/Table";
import { SystemTask, TaskStatus } from "../../api/SystemTask";

@customElement("ak-system-task-list")
export class SystemTaskListPage extends TablePage<SystemTask> {
    searchEnabled(): boolean {
        return false;
    }
    pageTitle(): string {
        return gettext("System Tasks");
    }
    pageDescription(): string {
        return gettext("Long-running operations which authentik executes in the background.");
    }
    pageIcon(): string {
        return gettext("pf-icon pf-icon-automation");
    }

    @property()
    order = "slug";

    apiEndpoint(page: number): Promise<AKResponse<SystemTask>> {
        return SystemTask.list({
            ordering: this.order,
            page: page,
        }).then((tasks) => {
            return {
                pagination: {
                    count: tasks.length,
                    total_pages: 1,
                    start_index: 0,
                    end_index: tasks.length,
                    current: 1,
                },
                results: tasks,
            };
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn("Identifier", "task_name"),
            new TableColumn("Description"),
            new TableColumn("Last run"),
            new TableColumn("Status"),
            new TableColumn("Messages"),
            new TableColumn(""),
        ];
    }

    taskStatus(task: SystemTask): TemplateResult {
        switch (task.status) {
            case TaskStatus.SUCCESSFUL:
                return html`<i class="fas fa-check pf-m-success" > </i> ${gettext("Successful")}`;
            case TaskStatus.WARNING:
                return html`<i class="fas fa-exclamation-triangle pf-m-warning" > </i> ${gettext("Warning")}`;
            case TaskStatus.ERROR:
                return html`<i class="fas fa-times pf-m-danger" > </i> ${gettext("Error")}`;
            default:
                return html`<i class="fas fa-question-circle" > </i> ${gettext("Unknown")}`;
        }
    }

    row(item: SystemTask): TemplateResult[] {
        return [
            html`${item.task_name}`,
            html`${item.task_description}`,
            html`${new Date(item.task_finish_timestamp * 1000).toLocaleString()}`,
            this.taskStatus(item),
            html`${item.messages.map(m => {
                return html`<li>${m}</li>`;
            })}`,
            html`<ak-action-button url=${SystemTask.retry(item.task_name)}>
                ${gettext("Retry Task")}
            </ak-action-button>`,
        ];
    }

}
