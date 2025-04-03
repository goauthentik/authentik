import "@goauthentik/admin/policies/BoundPoliciesList";
import "@goauthentik/admin/providers/rac/EndpointForm";
import "@goauthentik/admin/rbac/ObjectPermissionModal";
import "@goauthentik/admin/system-tasks/TaskList";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { getRelativeTime } from "@goauthentik/common/utils";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import { PaginatedResponse, Table } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

import { Schedule, TasksApi } from "@goauthentik/api";

@customElement("ak-schedule-list")
export class ScheduleList extends Table<Schedule> {
    expandable = true;
    clearOnRefresh = true;

    searchEnabled(): boolean {
        return true;
    }

    @property()
    order = "next_run";

    static get styles(): CSSResult[] {
        return super.styles.concat(PFDescriptionList);
    }

    async apiEndpoint(): Promise<PaginatedResponse<Schedule>> {
        return new TasksApi(DEFAULT_CONFIG).tasksSchedulesList({
            ...(await this.defaultEndpointConfig()),
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Schedule")),
            new TableColumn(msg("Crontab")),
            new TableColumn(msg("Next run")),
            new TableColumn(msg("Actions")),
        ];
    }

    row(item: Schedule): TemplateResult[] {
        return [
            html`<div>${item.description}</div>
                <small>${item.uid.replace(new RegExp("^authentik."), "")}</small>`,
            html`${item.crontab}`,
            html`<div>${getRelativeTime(item.nextRun)}</div>
                <small>${item.nextRun.toLocaleString()}</small>`,
            html``,
        ];
    }

    renderExpanded(item: Schedule): TemplateResult {
        return html` <td role="cell" colspan="3">
            <div class="pf-c-table__expandable-row-content">
                <div class="pf-c-content">
                    <ak-task-list .schedule=${item}></ak-task-list>
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
