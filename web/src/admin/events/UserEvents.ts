import "#components/ak-event-info";

import { SimpleEventTable } from "#admin/events/SimpleEventTable";

import { EventsEventsListRequest } from "@goauthentik/api";

import { customElement, property } from "lit/decorators.js";

@customElement("ak-events-user")
export class UserEvents extends SimpleEventTable {
    @property()
    targetUser!: string;

    async apiParameters(): Promise<Partial<EventsEventsListRequest>> {
        return {
            username: this.targetUser,
        };
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-events-user": UserEvents;
    }
}
