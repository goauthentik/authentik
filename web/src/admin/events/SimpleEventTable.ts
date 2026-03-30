import "#components/ak-event-info";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EventWithContext } from "#common/events";
import { actionToLabel } from "#common/labels";

import { PaginatedResponse, RowType, Table, TableColumn, Timestamp } from "#elements/table/Table";

import { EventGeo, renderEventUser } from "#admin/events/utils";

import { Event, EventsApi, EventsEventsListRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit-html";
import { property } from "lit/decorators.js";

export abstract class SimpleEventTable extends Table<Event> {
    abstract apiParameters(): Promise<Partial<EventsEventsListRequest>>;

    pageSize = 10;

    @property()
    order = "-created";

    expandable = true;

    async apiEndpoint(): Promise<PaginatedResponse<Event>> {
        return new EventsApi(DEFAULT_CONFIG).eventsEventsList({
            ...(await this.defaultEndpointConfig()),
            pageSize: this.pageSize,
            ...(await this.apiParameters()),
        });
    }

    protected override rowLabel(item: Event): string {
        return actionToLabel(item.action);
    }

    protected columns: TableColumn[] = [
        [msg("Action"), "action"],
        [msg("User"), "enabled"],
        [msg("Creation Date"), "created"],
        [msg("Client IP"), "client_ip"],
    ];

    row(item: EventWithContext): RowType[] {
        return [
            html`<div><a href="${`#/events/log/${item.pk}`}">${actionToLabel(item.action)}</a></div>
                <small>${item.app}</small>`,
            renderEventUser(item),
            [Timestamp(item.created), { style: "white-space: nowrap;" }],
            [
                html`<div>${item.clientIp || msg("-")}</div>
                    <small>${EventGeo(item)}</small>`,
                { style: "white-space: nowrap;" },
            ],
        ];
    }

    renderExpanded(item: Event): TemplateResult {
        return html`<ak-event-info .event=${item as EventWithContext}></ak-event-info>`;
    }

    renderEmpty(): TemplateResult {
        return super.renderEmpty(
            html`<ak-empty-state
                ><span>${msg("No Events found.")}</span>
                <div slot="body">${msg("No matching events could be found.")}</div>
            </ak-empty-state>`,
        );
    }
}
