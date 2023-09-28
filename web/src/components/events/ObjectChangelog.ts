import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EventWithContext } from "@goauthentik/common/events";
import { uiConfig } from "@goauthentik/common/ui/config";
import "@goauthentik/components/ak-event-info";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/buttons/Dropdown";
import "@goauthentik/elements/buttons/ModalButton";
import "@goauthentik/elements/buttons/SpinnerButton";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { Table, TableColumn } from "@goauthentik/elements/table/Table";

import { msg, str } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { Event, EventsApi } from "@goauthentik/api";

@customElement("ak-object-changelog")
export class ObjectChangelog extends Table<Event> {
    expandable = true;

    @property()
    order = "-created";

    @property()
    targetModelPk!: string | number;

    @property()
    targetModelApp?: string;

    private _targetModelName = "";

    @property()
    set targetModelName(value: string) {
        this._targetModelName = value;
        this.fetch();
    }

    get targetModelName(): string {
        return this._targetModelName;
    }

    async apiEndpoint(page: number): Promise<PaginatedResponse<Event>> {
        let modelName = this._targetModelName;
        let appName = this.targetModelApp;
        if (this._targetModelName.indexOf(".") !== -1) {
            const parts = this._targetModelName.split(".");
            appName = parts[0];
            modelName = parts[1];
        }
        if (this._targetModelName === "") {
            return Promise.reject();
        }
        return new EventsApi(DEFAULT_CONFIG).eventsEventsList({
            action: "model_",
            page: page,
            ordering: this.order,
            pageSize: (await uiConfig()).pagination.perPage,
            contextModelApp: appName,
            contextModelName: modelName,
            contextModelPk: this.targetModelPk.toString(),
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Action"), "action"),
            new TableColumn(msg("User"), "enabled"),
            new TableColumn(msg("Creation Date"), "created"),
            new TableColumn(msg("Client IP"), "client_ip"),
        ];
    }

    row(item: EventWithContext): TemplateResult[] {
        return [
            html`${item.action}`,
            html`<div>${item.user?.username}</div>
                ${item.user.on_behalf_of
                    ? html`<small>
                          ${msg(str`On behalf of ${item.user.on_behalf_of.username}`)}
                      </small>`
                    : html``}`,
            html`<span>${item.created?.toLocaleString()}</span>`,
            html`<span>${item.clientIp || msg("-")}</span>`,
        ];
    }

    renderExpanded(item: Event): TemplateResult {
        return html` <td role="cell" colspan="4">
                <div class="pf-c-table__expandable-row-content">
                    <ak-event-info .event=${item as EventWithContext}></ak-event-info>
                </div>
            </td>
            <td></td>
            <td></td>
            <td></td>`;
    }

    renderEmpty(): TemplateResult {
        return super.renderEmpty(
            html`<ak-empty-state header=${msg("No Events found.")}>
                <div slot="body">${msg("No matching events could be found.")}</div>
            </ak-empty-state>`,
        );
    }
}
