import "#components/ak-event-info";
import "#elements/Tabs";
import "#elements/buttons/Dropdown";
import "#elements/buttons/ModalButton";
import "#elements/buttons/SpinnerButton/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EventWithContext } from "#common/events";
import { actionToLabel } from "#common/labels";
import { formatElapsedTime } from "#common/temporal";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { renderEventUser } from "#admin/events/utils";

import { Event, EventsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-events-user")
export class UserEvents extends Table<Event> {
    public override expandable = true;

    @property()
    public override order = "-created";

    @property()
    public targetUser!: string;

    protected async apiEndpoint(): Promise<PaginatedResponse<Event>> {
        return new EventsApi(DEFAULT_CONFIG).eventsEventsList({
            ...(await this.defaultEndpointConfig()),
            username: this.targetUser,
        });
    }

    protected columns(): TableColumn[] {
        return [
            new TableColumn(msg("Action"), "action"),
            new TableColumn(msg("User"), "enabled"),
            new TableColumn(msg("Creation Date"), "created"),
            new TableColumn(msg("Client IP"), "client_ip"),
        ];
    }

    protected row(item: EventWithContext): SlottedTemplateResult[] {
        return [
            html`${actionToLabel(item.action)}`,
            renderEventUser(item),
            html`<div>${formatElapsedTime(item.created)}</div>
                <small>${item.created.toLocaleString()}</small>`,
            html`<span>${item.clientIp || msg("-")}</span>`,
        ];
    }

    protected override renderExpanded(item: Event): TemplateResult {
        return html` <td role="cell" colspan="4">
                <div class="pf-c-table__expandable-row-content">
                    <ak-event-info .event=${item as EventWithContext}></ak-event-info>
                </div>
            </td>
            <td></td>
            <td></td>
            <td></td>`;
    }

    protected override renderEmpty(): TemplateResult {
        return super.renderEmpty(
            html`<ak-empty-state
                ><span>${msg("No Events found.")}</span>
                <div slot="body">${msg("No matching events could be found.")}</div>
            </ak-empty-state>`,
        );
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-events-user": UserEvents;
    }
}
