import "#admin/rbac/ObjectPermissionModal";
import "#elements/buttons/ActionButton/index";
import "#elements/buttons/SpinnerButton/index";
import "#elements/events/LogViewer";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/tasks/TaskStatus";
import "#elements/tasks/TaskStatusSummary";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";

import { PaginatedResponse, Table, TableColumn, Timestamp } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import {
    GlobalTaskStatus,
    Task,
    TasksApi,
    TasksTasksListAggregatedStatusEnum,
    TasksTasksListStateEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFSpacing from "@patternfly/patternfly/utilities/Spacing/spacing.css";

@customElement("ak-task-list")
export class TaskList extends Table<Task> {
    public static styles: CSSResult[] = [
        // ---
        ...super.styles,
        PFDescriptionList,
        PFSpacing,
        PFTitle,
    ];

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

    @property({ type: Boolean, attribute: "include-overview" })
    includeOverview: boolean = false;

    protected override searchEnabled = true;

    @property()
    order = "-mtime";

    @state()
    status?: GlobalTaskStatus;

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
                  TasksTasksListAggregatedStatusEnum.Preprocess,
                  TasksTasksListAggregatedStatusEnum.Running,
                  TasksTasksListAggregatedStatusEnum.Postprocess,
                  TasksTasksListAggregatedStatusEnum.Rejected,
                  TasksTasksListAggregatedStatusEnum.Warning,
                  TasksTasksListAggregatedStatusEnum.Error,
              ]
            : undefined;
        if (this.includeOverview) {
            this.status = await new TasksApi(DEFAULT_CONFIG).tasksTasksStatusRetrieve();
        }
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

    protected override rowLabel(item: Task): string | null {
        return item.description ?? item.actorName ?? null;
    }

    protected columns: TableColumn[] = [
        [msg("Task"), "actor_name"],
        [msg("Queue"), "queue_name"],
        [msg("Retries"), "retries"],
        [msg("Planned execution time")],
        [msg("Last updated"), "mtime"],
        [msg("Status"), "aggregated_status"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    render(): TemplateResult {
        return html`${this.includeOverview
            ? html`<ak-task-status-summary .status=${this.status}></ak-task-status-summary>`
            : nothing}${super.render()}`;
    }

    renderToolbarAfter(): TemplateResult {
        return html`<div class="pf-c-toolbar__group pf-m-filter-group">
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
                        <span class="pf-c-switch__label"> ${msg("Exclude successful tasks")} </span>
                    </label>
                </div>
            </div>
        </div>`;
    }

    row(item: Task): SlottedTemplateResult[] {
        return [
            html`<div>${item.description}</div>
                <small>${item.uid}</small>`,
            html`${item.queueName}`,
            html`${item.retries}`,
            item.eta !== undefined ? Timestamp(item.eta) : nothing,
            Timestamp(item.mtime ?? new Date()),
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
                : nothing,
        ];
    }

    renderExpanded(item: Task): TemplateResult {
        return html`<div class="pf-c-content">
            <p class="pf-c-title pf-u-mb-md">${msg("Current execution logs")}</p>
            <ak-log-viewer .logs=${item?.logs}></ak-log-viewer>
            <p class="pf-c-title pf-u-mt-xl pf-u-mb-md">${msg("Previous executions logs")}</p>
            <ak-log-viewer .logs=${item?.previousLogs}></ak-log-viewer>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-task-list": TaskList;
    }
}
