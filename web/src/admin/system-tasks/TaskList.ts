import { EVENT_REFRESH } from "#common/constants";
import { formatElapsedTime } from "#common/temporal";
import "@goauthentik/admin/rbac/ObjectPermissionModal";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { PFColor } from "@goauthentik/elements/Label";
import "@goauthentik/elements/buttons/ActionButton";
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

import {
    Task,
    TasksApi,
    TasksTasksListAggregatedStatusEnum,
    TasksTasksListStateEnum,
} from "@goauthentik/api";

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

    @property()
    excludeSuccessful: boolean = true;

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
        const aggregatedStatus = this.excludeSuccessful
            ? [
                  TasksTasksListAggregatedStatusEnum.Queued,
                  TasksTasksListAggregatedStatusEnum.Consumed,
                  TasksTasksListAggregatedStatusEnum.Rejected,
                  TasksTasksListAggregatedStatusEnum.Warning,
                  TasksTasksListAggregatedStatusEnum.Error,
              ]
            : undefined;
        return new TasksApi(DEFAULT_CONFIG).tasksTasksList({
            ...(await this.defaultEndpointConfig()),
            relObjContentTypeAppLabel: this.relObjAppLabel,
            relObjContentTypeModel: this.relObjModel,
            relObjId: this.relObjId,
            relObjIdIsnull,
            aggregatedStatus,
        });
    }

    #toggleShowOnlyStandalone = () => {
        this.showOnlyStandalone = !this.showOnlyStandalone;
        this.page = 1;
        return this.fetch();
    };

    #toggleExcludeSuccessful = () => {
        this.excludeSuccessful = !this.excludeSuccessful;
        this.page = 1;
        return this.fetch();
    };

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Task"), "actor_name"),
            new TableColumn(msg("Queue"), "queue_name"),
            new TableColumn(msg("Last updated"), "mtime"),
            new TableColumn(msg("Status"), "aggregated_status"),
            new TableColumn(msg("Actions")),
        ];
    }

    renderToolbarAfter(): TemplateResult {
        return html`&nbsp;
            <div class="pf-c-toolbar__group pf-m-filter-group">
                <div class="pf-c-toolbar__item pf-m-search-filter">
                    <div class="pf-c-input-group">
                        ${this.relObjId === undefined
                            ? html` <label class="pf-c-switch">
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
                              </label>`
                            : html``}
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${this.excludeSuccessful}
                                @change=${this.#toggleExcludeSuccessful}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria - hidden="true"> </i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">
                                ${msg("Exclude successful tasks")}
                            </span>
                        </label>
                    </div>
                </div>
            </div>`;
    }

    taskState(task: Task): TemplateResult {
        switch (task.aggregatedStatus) {
            case TasksTasksListAggregatedStatusEnum.Queued:
                return html`<ak-label color=${PFColor.Grey}>${msg("Waiting to run")}</ak-label>`;
            case TasksTasksListAggregatedStatusEnum.Consumed:
                return html`<ak-label color=${PFColor.Blue}>${msg("Running")}</ak-label>`;
            case TasksTasksListAggregatedStatusEnum.Done:
            case TasksTasksListAggregatedStatusEnum.Info:
                return html`<ak-label color=${PFColor.Green}>${msg("Successful")}</ak-label>`;
            case TasksTasksListAggregatedStatusEnum.Warning:
                return html`<ak-label color=${PFColor.Orange}>${msg("Warning")}</ak-label>`;
            case TasksTasksListAggregatedStatusEnum.Rejected:
            case TasksTasksListAggregatedStatusEnum.Error:
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
            [TasksTasksListStateEnum.Rejected, TasksTasksListStateEnum.Done].includes(item.state)
                ? html`<ak-action-button
                      class="pf-m-plain"
                      .apiRequest=${() => {
                          return new TasksApi(DEFAULT_CONFIG)
                              .tasksTasksRetryCreate({
                                  messageId: item.messageId,
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
                      <pf-tooltip position="top" content=${msg("Retry task")}>
                          <i class="fas fa-redo" aria-hidden="true"></i>
                      </pf-tooltip>
                  </ak-action-button>`
                : html``,
        ];
    }

    renderExpanded(item: Task): TemplateResult {
        return html` <td role="cell" colspan="3">
            <div class="pf-c-table__expandable-row-content">
                <div class="pf-c-content">
                    <p>Current execution logs</p>
                    <ak-log-viewer .logs=${item?.messages}></ak-log-viewer>
                    <p>Previous executions logs</p>
                    <ak-log-viewer .logs=${item?.previousMessages}></ak-log-viewer>
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
