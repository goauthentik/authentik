import "#elements/buttons/ActionButton/index";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#components/tasks/ScheduleForm";
import "#components/tasks/TaskList";
import "#components/tasks/TaskStatus";
import "#elements/table/ak-table-filter-select";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { aki } from "#common/api/client";
import { EVENT_REFRESH } from "#common/constants";

import { FilterOption } from "#elements/table/ak-table-filter-select";
import { PaginatedResponse, Table, TableColumn, Timestamp } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { ModelEnum, Schedule, TasksApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

@customElement("ak-schedule-list")
export class ScheduleList extends Table<Schedule> {
    public static styles: CSSResult[] = [
        // ---
        ...super.styles,
        PFDescriptionList,
    ];

    expandable = true;
    clearOnRefresh = true;

    protected override searchEnabled = true;

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

    async apiEndpoint(): Promise<PaginatedResponse<Schedule>> {
        const relObjIdIsnull =
            typeof this.relObjId !== "undefined"
                ? undefined
                : this.showOnlyStandalone
                  ? true
                  : undefined;
        return aki(TasksApi).tasksSchedulesList({
            ...(await this.defaultEndpointConfig()),
            relObjContentTypeAppLabel: this.relObjAppLabel,
            relObjContentTypeModel: this.relObjModel,
            relObjId: this.relObjId,
            relObjIdIsnull,
        });
    }

    protected override rowLabel(item: Schedule): string | null {
        return item.description ?? item.actorName ?? null;
    }

    protected columns: TableColumn[] = [
        [msg("Schedule"), "actor_name"],
        [msg("Crontab"), "crontab"],
        [msg("Next run"), "next_run"],
        [msg("Last status")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    renderToolbarAfter(): SlottedTemplateResult {
        if (this.relObjId !== undefined) {
            return nothing;
        }
        return html`<div class="pf-c-toolbar__group pf-m-filter-group">
            <div class="pf-c-toolbar__item pf-m-search-filter">
                <ak-table-filter-select
                    .options=${[
                        { label: msg("Show only standalone schedules"), value: true },
                        { label: msg("Show all schedules"), value: false },
                    ]}
                    group=${msg("Standalone")}
                    .value=${this.showOnlyStandalone}
                    @change=${(ev: CustomEvent<FilterOption<boolean>>) => {
                        this.showOnlyStandalone = ev.detail.value;
                        this.page = 1;
                        this.fetch();
                    }}
                ></ak-table-filter-select>
            </div>
        </div>`;
    }

    row(item: Schedule): SlottedTemplateResult[] {
        return [
            html`<div>${item.description}</div>
                <small>${item.uid}</small>`,
            html`${item.crontab}`,
            html` ${item.paused ? html`${msg("Paused")}` : Timestamp(item.nextRun)} `,
            html`<ak-task-status .status=${item.lastTaskStatus}></ak-task-status>`,
            html`<ak-action-button
                    class="pf-m-plain"
                    .apiRequest=${() => {
                        return aki(TasksApi)
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
                    <span slot="submit">${msg("Save Changes")}</span>
                    <span slot="header">${msg("Update Schedule")}</span>
                    <ak-schedule-form slot="form" .instancePk=${item.id}> </ak-schedule-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit" aria-hidden="true"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>`,
        ];
    }

    renderExpanded(item: Schedule): TemplateResult {
        const [appLabel, modelName] = ModelEnum.AuthentikTasksSchedulesSchedule.split(".");
        return html`<div class="pf-c-content">
            <ak-task-list
                .relObjAppLabel=${appLabel}
                .relObjModel=${modelName}
                .relObjId="${item.id}"
            ></ak-task-list>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-schedule-list": ScheduleList;
    }
}
