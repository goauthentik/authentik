import "#elements/buttons/ActionButton/index";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/tasks/ScheduleForm";
import "#elements/tasks/TaskList";
import "#elements/tasks/TaskStatus";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";
import { formatElapsedTime } from "#common/temporal";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";

import { ModelEnum, Schedule, TasksApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

@customElement("ak-schedule-list")
export class ScheduleList extends Table<Schedule> {
    expandable = true;
    clearOnRefresh = true;

    searchEnabled(): boolean {
        return true;
    }

    @property()
    order = "next_run";

    @property()
    relObjAppLabel?: string;
    @property()
    relObjModel?: string;
    @property()
    relObjId?: string;

    @property({ type: Boolean })
    showOnlyStandalone: boolean = true;

    static get styles(): CSSResult[] {
        return super.styles.concat(PFDescriptionList);
    }

    async apiEndpoint(): Promise<PaginatedResponse<Schedule>> {
        const relObjIdIsnull =
            typeof this.relObjId !== "undefined"
                ? undefined
                : this.showOnlyStandalone
                  ? true
                  : undefined;
        return new TasksApi(DEFAULT_CONFIG).tasksSchedulesList({
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
            new TableColumn(msg("Schedule"), "actor_name"),
            new TableColumn(msg("Crontab"), "crontab"),
            new TableColumn(msg("Next run"), "next_run"),
            new TableColumn(msg("Last status")),
            new TableColumn(msg("Actions")),
        ];
    }

    renderToolbarAfter(): TemplateResult {
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
                                    <i class="fas fa-check" aria-hidden="true"> </i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">
                                ${msg("Show only standalone schedules")}
                            </span>
                        </label>
                    </div>
                </div>
            </div>`;
    }

    row(item: Schedule): TemplateResult[] {
        return [
            html`<div>${item.description}</div>
                <small>${item.uid}</small>`,
            html`${item.crontab}`,
            html`
                ${item.paused
                    ? html`Paused`
                    : html`
                          <div>${formatElapsedTime(item.nextRun)}</div>
                          <small>${item.nextRun.toLocaleString()}</small>
                      `}
            `,
            html`<ak-task-status .status=${item.lastTaskStatus}></ak-task-status>`,
            html`<ak-action-button
                    class="pf-m-plain"
                    .apiRequest=${() => {
                        return new TasksApi(DEFAULT_CONFIG)
                            .tasksSchedulesSendCreate({
                                id: item.id,
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
                    <pf-tooltip position="top" content=${msg("Run scheduled task now")}>
                        <i class="fas fa-play" aria-hidden="true"></i>
                    </pf-tooltip>
                </ak-action-button>
                <ak-forms-modal>
                    <span slot="submit"> ${msg("Update")} </span>
                    <span slot="header"> ${msg("Update Schedule")} </span>
                    <ak-schedule-form slot="form" .instancePk=${item.id}> </ak-schedule-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>`,
        ];
    }

    renderExpanded(item: Schedule): TemplateResult {
        const [appLabel, modelName] = ModelEnum.AuthentikTasksSchedulesSchedule.split(".");
        return html` <td role="cell" colspan="3">
            <div class="pf-c-table__expandable-row-content">
                <div class="pf-c-content">
                    <ak-task-list
                        .relObjAppLabel=${appLabel}
                        .relObjModel=${modelName}
                        .relObjId="${item.id}"
                    ></ak-task-list>
                </div>
            </div>
        </td>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-schedule-list": ScheduleList;
    }
}
