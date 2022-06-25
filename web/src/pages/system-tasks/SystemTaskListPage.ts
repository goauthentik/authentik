import { AKResponse } from "@goauthentik/web/api/Client";
import { DEFAULT_CONFIG } from "@goauthentik/web/api/Config";
import { EVENT_REFRESH } from "@goauthentik/web/constants";
import { PFColor } from "@goauthentik/web/elements/Label";
import "@goauthentik/web/elements/buttons/ActionButton";
import "@goauthentik/web/elements/buttons/SpinnerButton";
import { TableColumn } from "@goauthentik/web/elements/table/Table";
import { TablePage } from "@goauthentik/web/elements/table/TablePage";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

import { AdminApi, StatusEnum, Task } from "@goauthentik/api";

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

    async apiEndpoint(page: number): Promise<AKResponse<Task>> {
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
            new TableColumn(t`Identifier`),
            new TableColumn(t`Description`),
            new TableColumn(t`Last run`),
            new TableColumn(t`Status`),
            new TableColumn(t`Actions`),
        ];
    }

    taskStatus(task: Task): TemplateResult {
        switch (task.status) {
            case StatusEnum.Successful:
                return html`<ak-label color=${PFColor.Green}>${t`Successful`}</ak-label>`;
            case StatusEnum.Warning:
                return html`<ak-label color=${PFColor.Orange}>${t`Warning`}</ak-label>`;
            case StatusEnum.Error:
                return html`<ak-label color=${PFColor.Red}>${t`Error`}</ak-label>`;
            default:
                return html`<ak-label color=${PFColor.Grey}>${t`Unknown`}</ak-label>`;
        }
    }

    renderExpanded(item: Task): TemplateResult {
        return html` <td role="cell" colspan="3">
                <div class="pf-c-table__expandable-row-content">
                    <dl class="pf-c-description-list pf-m-horizontal">
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text">${t`Messages`}</span>
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">
                                    ${item.messages.map((m) => {
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
                class="pf-m-plain"
                .apiRequest=${() => {
                    return new AdminApi(DEFAULT_CONFIG)
                        .adminSystemTasksRetryCreate({
                            id: item.taskName,
                        })
                        .then(() => {
                            this.dispatchEvent(
                                new CustomEvent(EVENT_REFRESH, {
                                    bubbles: true,
                                    composed: true,
                                }),
                            );
                        });
                }}
            >
                <i class="fas fa-sync-alt" aria-hidden="true"></i>
            </ak-action-button>`,
        ];
    }
}
