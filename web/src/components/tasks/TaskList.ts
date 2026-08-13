import "#elements/buttons/ActionButton/index";
import "#elements/buttons/SpinnerButton/index";
import "#elements/events/LogViewer";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#components/tasks/TaskStatus";
import "#components/tasks/TaskStatusSummary";
import "#elements/table/ak-table-filter-select";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { aki } from "#common/api/client";
import { EVENT_REFRESH } from "#common/constants";

import { FilterOption } from "#elements/table/ak-table-filter-select";
import { PaginatedResponse, Table, TableColumn, Timestamp } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import {
    GlobalTaskStatus,
    Task,
    TaskAggregatedStatusEnum,
    TasksApi,
    TaskStatusEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFSpacing from "@patternfly/patternfly/utilities/Spacing/spacing.css";

/**
 * TaskList
 *
 * @summary Displays lists of running tasks performed by the authentik service. Often specialized to
 * a specific object types within the service, or even individual objects.
 *
 */

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
    relObjId?: string | number;

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
                  TaskAggregatedStatusEnum.WaitingForDependencies,
                  TaskAggregatedStatusEnum.Queued,
                  TaskAggregatedStatusEnum.Consumed,
                  TaskAggregatedStatusEnum.Preprocess,
                  TaskAggregatedStatusEnum.Running,
                  TaskAggregatedStatusEnum.Postprocess,
                  TaskAggregatedStatusEnum.Rejected,
                  TaskAggregatedStatusEnum.Warning,
                  TaskAggregatedStatusEnum.Error,
              ]
            : undefined;
        if (this.includeOverview) {
            this.status = await aki(TasksApi).tasksTasksStatusRetrieve();
        }
        return aki(TasksApi).tasksTasksList({
            ...(await this.defaultEndpointConfig()),
            relObjContentTypeAppLabel: this.relObjAppLabel,
            relObjContentTypeModel: this.relObjModel,
            relObjId: this.relObjId ? this.relObjId.toString() : undefined,
            relObjIdIsnull,
            aggregatedStatus,
        });
    }

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
                ${this.relObjId === undefined
                    ? html`<ak-table-filter-select
                          .options=${[
                              { label: msg("Show only standalone tasks"), value: true },
                              { label: msg("Show all tasks"), value: false },
                          ]}
                          group=${msg("Standalone")}
                          .value=${this.showOnlyStandalone}
                          @change=${(ev: CustomEvent<FilterOption<boolean>>) => {
                              this.showOnlyStandalone = ev.detail.value;
                              this.page = 1;
                              this.fetch();
                          }}
                      ></ak-table-filter-select>`
                    : nothing}
            </div>
            <div class="pf-c-toolbar__item pf-m-search-filter">
                <ak-table-filter-select
                    .options=${[
                        { label: msg("Exclude successful tasks"), value: true },
                        { label: msg("Include successful tasks"), value: false },
                    ]}
                    group=${msg("Successful tasks")}
                    .value=${this.excludeSuccessful}
                    @change=${(ev: CustomEvent<FilterOption<boolean>>) => {
                        this.excludeSuccessful = ev.detail.value;
                        this.page = 1;
                        this.fetch();
                    }}
                ></ak-table-filter-select>
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
            html`<ak-task-status status=${item.aggregatedStatus}></ak-task-status>`,
            item.state === TaskStatusEnum.Rejected
                ? html`<ak-action-button
                      class="pf-m-plain"
                      .apiRequest=${() => {
                          return aki(TasksApi)
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
            <ak-log-viewer display-box="contents" .items=${item.logs}></ak-log-viewer>
            ${item.previousLogs.length > 0
                ? html`<p class="pf-c-title pf-u-mt-xl pf-u-mb-md">
                          ${msg("Previous executions logs")}
                      </p>
                      <ak-log-viewer
                          display-box="contents"
                          .items=${item.previousLogs}
                      ></ak-log-viewer>`
                : nothing}
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-task-list": TaskList;
    }
}
