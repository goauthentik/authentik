import "#elements/buttons/ActionButton/index";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#admin/tasks/ScheduleForm";
import "#admin/tasks/TaskList";
import "#admin/tasks/TaskStatus";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";

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
                    <span slot="submit">${msg("Update")}</span>
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
