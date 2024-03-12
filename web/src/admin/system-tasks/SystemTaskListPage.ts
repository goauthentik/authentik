import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { uiConfig } from "@goauthentik/common/ui/config";
import { getRelativeTime } from "@goauthentik/common/utils";
import { PFColor } from "@goauthentik/elements/Label";
import "@goauthentik/elements/buttons/ActionButton";
import "@goauthentik/elements/buttons/SpinnerButton";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

import { EventsApi, SystemTask, SystemTaskStatusEnum } from "@goauthentik/api";

@customElement("ak-system-task-list")
export class SystemTaskListPage extends TablePage<SystemTask> {
    pageTitle(): string {
        return msg("System Tasks");
    }
    pageDescription(): string {
        return msg("Long-running operations which authentik executes in the background.");
    }
    pageIcon(): string {
        return "pf-icon pf-icon-automation";
    }

    expandable = true;

    searchEnabled(): boolean {
        return true;
    }

    @property()
    order = "name";

    static get styles(): CSSResult[] {
        return super.styles.concat(PFDescriptionList);
    }

    async apiEndpoint(page: number): Promise<PaginatedResponse<SystemTask>> {
        return new EventsApi(DEFAULT_CONFIG).eventsSystemTasksList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Identifier"), "name"),
            new TableColumn(msg("Description")),
            new TableColumn(msg("Last run")),
            new TableColumn(msg("Status"), "status"),
            new TableColumn(msg("Actions")),
        ];
    }

    taskStatus(task: SystemTask): TemplateResult {
        switch (task.status) {
            case SystemTaskStatusEnum.Successful:
                return html`<ak-label color=${PFColor.Green}>${msg("Successful")}</ak-label>`;
            case SystemTaskStatusEnum.Warning:
                return html`<ak-label color=${PFColor.Orange}>${msg("Warning")}</ak-label>`;
            case SystemTaskStatusEnum.Error:
                return html`<ak-label color=${PFColor.Red}>${msg("Error")}</ak-label>`;
            default:
                return html`<ak-label color=${PFColor.Grey}>${msg("Unknown")}</ak-label>`;
        }
    }

    renderExpanded(item: SystemTask): TemplateResult {
        return html` <td role="cell" colspan="3">
                <div class="pf-c-table__expandable-row-content">
                    <dl class="pf-c-description-list pf-m-horizontal">
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text">${msg("Duration")}</span>
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">
                                    ${msg(str`${item.duration.toFixed(2)} seconds`)}
                                </div>
                            </dd>
                        </div>
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text">${msg("Messages")}</span>
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

    row(item: SystemTask): TemplateResult[] {
        return [
            html`<pre>${item.name}${item.uid ? `:${item.uid}` : ""}</pre>`,
            html`${item.description}`,
            html`<div>${getRelativeTime(item.finishTimestamp)}</div>
                <small>${item.finishTimestamp.toLocaleString()}</small>`,
            this.taskStatus(item),
            html`<ak-action-button
                class="pf-m-plain"
                .apiRequest=${() => {
                    return new EventsApi(DEFAULT_CONFIG)
                        .eventsSystemTasksRunCreate({
                            uuid: item.uuid,
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
                <pf-tooltip position="top" content=${msg("Restart task")}>
                    <i class="fas fa-redo" aria-hidden="true"></i>
                </pf-tooltip>
            </ak-action-button>`,
        ];
    }
}
