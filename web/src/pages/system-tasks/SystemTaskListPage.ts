import { t } from "@lingui/macro";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

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

    expandable = true;

    @property()
    order = "slug";

    static get styles(): CSSResult[] {
        return super.styles.concat(PFDescriptionList);
    }

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

    renderExpanded(item: Task): TemplateResult {
        return html`
        <td role="cell" colspan="3">
            <div class="pf-c-table__expandable-row-content">
                <dl class="pf-c-description-list pf-m-horizontal">
                    <div class="pf-c-description-list__group">
                        <dt class="pf-c-description-list__term">
                            <span class="pf-c-description-list__text">${t`Messages`}</span>
                        </dt>
                        <dd class="pf-c-description-list__description">
                            <div class="pf-c-description-list__text">
                                ${item.messages.map(m => {
                                    return html`<li>${m}</li>`;
                                })}
                            </div>
                        </dd>
                    </div>
                </dl>
            </div>
        </td>
        <td></td>
        <td></td>`;
    }

    row(item: Task): TemplateResult[] {
        return [
            html`${item.taskName}`,
            html`${item.taskDescription}`,
            html`${item.taskFinishTimestamp.toLocaleString()}`,
            this.taskStatus(item),
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
