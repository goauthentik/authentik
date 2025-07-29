import "#admin/rbac/ObjectPermissionModal";
import "#elements/buttons/ActionButton/index";
import "#elements/buttons/SpinnerButton/index";
import "#elements/events/LogViewer";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/tasks/TaskStatus";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";
import { formatElapsedTime } from "#common/temporal";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";

import {
    Task,
    TasksApi,
    TasksTasksListAggregatedStatusEnum,
    TasksTasksListStateEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFSpacing from "@patternfly/patternfly/utilities/Spacing/spacing.css";

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

    @property({ type: Boolean })
    showOnlyStandalone: boolean = true;

    @property({ type: Boolean })
    excludeSuccessful: boolean = true;

    searchEnabled(): boolean {
        return true;
    }

    @property()
    order = "-mtime";

    static get styles(): CSSResult[] {
        return super.styles.concat(PFDescriptionList, PFSpacing, PFTitle);
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
                                          <i class="fas fa-check" aria-hidden="true"> </i>
                                      </span>
                                  </span>
                                  <span class="pf-c-switch__label">
                                      ${msg("Show only standalone tasks")}
                                  </span>
                              </label>`
                            : nothing}
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${this.excludeSuccessful}
                                @change=${this.#toggleExcludeSuccessful}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"> </i>
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

    row(item: Task): TemplateResult[] {
        return [
            html`<div>${item.description}</div>
                <small>${item.uid}</small>`,
            html`${item.queueName}`,
            html`<div>${formatElapsedTime(item.mtime || new Date())}</div>
                <small>${item.mtime?.toLocaleString()}</small>`,
            html`<ak-task-status .status=${item.aggregatedStatus}></ak-task-status>`,
            item.state === TasksTasksListStateEnum.Rejected ||
            item.state === TasksTasksListStateEnum.Done
                ? html`<ak-action-button
                      class="pf-m-plain"
                      .apiRequest=${() => {
                          return new TasksApi(DEFAULT_CONFIG)
                              .tasksTasksRetryCreate({
                                  messageId: item.messageId ?? "",
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
        return html` <td role="cell" colspan="5">
            <div class="pf-c-table__expandable-row-content">
                <div class="pf-c-content">
                    <p class="pf-c-title pf-u-mb-md">${msg("Current execution logs")}</p>
                    <ak-log-viewer .logs=${item?.messages}></ak-log-viewer>
                    <p class="pf-c-title pf-u-mt-xl pf-u-mb-md">
                        ${msg("Previous executions logs")}
                    </p>
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
