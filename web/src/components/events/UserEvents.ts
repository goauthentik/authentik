import "#components/ak-event-info";
import "#elements/Tabs";
import "#elements/buttons/Dropdown";
import "#elements/buttons/ModalButton";
import "#elements/buttons/SpinnerButton/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EventWithContext } from "#common/events";
import { renderEventUser } from "#common/events/utils";
import { actionToLabel } from "#common/labels";

import { PaginatedResponse, Table, TableColumn, Timestamp } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { Event, EventsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-events-user")
export class UserEvents extends Table<Event> {
    expandable = true;

    @property()
    order = "-created";

    @property()
    targetUser!: string;

    async apiEndpoint(): Promise<PaginatedResponse<Event>> {
        return new EventsApi(DEFAULT_CONFIG).eventsEventsList({
            ...(await this.defaultEndpointConfig()),
            username: this.targetUser,
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

    row(item: EventWithContext): SlottedTemplateResult[] {
        return [
            html`${actionToLabel(item.action)}`,
            renderEventUser(item),
            Timestamp(item.created),
            html`<span>${item.clientIp || msg("-")}</span>`,
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

declare global {
    interface HTMLElementTagNameMap {
        "ak-events-user": UserEvents;
    }
}
