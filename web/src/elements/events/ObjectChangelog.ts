import { AKResponse } from "@goauthentik/web/api/Client";
import { DEFAULT_CONFIG } from "@goauthentik/web/api/Config";
import { EventWithContext } from "@goauthentik/web/api/Events";
import { uiConfig } from "@goauthentik/web/common/config";
import "@goauthentik/web/elements/Tabs";
import "@goauthentik/web/elements/buttons/Dropdown";
import "@goauthentik/web/elements/buttons/ModalButton";
import "@goauthentik/web/elements/buttons/SpinnerButton";
import { Table, TableColumn } from "@goauthentik/web/elements/table/Table";
import "@goauthentik/web/pages/events/EventInfo";

import { t } from "@lingui/macro";

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

    async apiEndpoint(page: number): Promise<AKResponse<Event>> {
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
            new TableColumn(t`Action`, "action"),
            new TableColumn(t`User`, "enabled"),
            new TableColumn(t`Creation Date`, "created"),
            new TableColumn(t`Client IP`, "client_ip"),
        ];
    }

    row(item: EventWithContext): TemplateResult[] {
        return [
            html`${item.action}`,
            html`<div>${item.user?.username}</div>
                ${item.user.on_behalf_of
                    ? html`<small> ${t`On behalf of ${item.user.on_behalf_of.username}`} </small>`
                    : html``}`,
            html`<span>${item.created?.toLocaleString()}</span>`,
            html`<span>${item.clientIp || t`-`}</span>`,
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
        return super.renderEmpty(html`<ak-empty-state header=${t`No Events found.`}>
            <div slot="body">${t`No matching events could be found.`}</div>
        </ak-empty-state>`);
    }
}
