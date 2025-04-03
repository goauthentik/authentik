import "@goauthentik/admin/policies/BoundPoliciesList";
import "@goauthentik/admin/providers/rac/EndpointForm";
import "@goauthentik/admin/rbac/ObjectPermissionModal";
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

import { Schedule, Task, TasksApi } from "@goauthentik/api";

@customElement("ak-task-list")
export class TaskList extends Table<Task> {
    expandable = true;
    clearOnRefresh = true;

    @property()
    schedule: Schedule | undefined;

    searchEnabled(): boolean {
        return true;
    }

    @property()
    order = "-mtime";

    static get styles(): CSSResult[] {
        return super.styles.concat(PFDescriptionList);
    }

    async apiEndpoint(): Promise<PaginatedResponse<Task>> {
        const excludeScheduled = this.schedule === undefined;
        return new TasksApi(DEFAULT_CONFIG).tasksTasksList({
            ...(await this.defaultEndpointConfig()),
            excludeScheduled: excludeScheduled,
            scheduleUid: this.schedule?.uid,
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Task")),
            new TableColumn(msg("Queue")),
            new TableColumn(msg("Last updated")),
            new TableColumn(msg("Actions")),
        ];
    }

    row(item: Task): TemplateResult[] {
        return [
            html`<div>${item.actorName}</div>
                <small>${item.uid}</small>`,
            html`${item.queueName}`,
            html`<div>${getRelativeTime(item.mtime)}</div>
                <small>${item.mtime.toLocaleString()}</small>`,
            html``,
        ];
    }

    renderExpanded(item: Task): TemplateResult {
        return html` <td></td>
            <td role="cell" colspan="12">
                <div class="pf-c-table__expandable-row-content">
                    <div class="pf-c-content">
                        <p>TODO: ${item.actorName}</p>
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
