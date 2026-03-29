import "#components/ak-event-info";

import { SimpleEventTable } from "#admin/events/SimpleEventTable";

import { EventsEventsListRequest } from "@goauthentik/api";

import { customElement, property } from "lit/decorators.js";

@customElement("ak-events-application")
export class ApplicationEvents extends SimpleEventTable {
    @property({ attribute: "application-id" })
    applicationId!: string;

    async apiParameters(): Promise<Partial<EventsEventsListRequest>> {
        return {
            contextAuthorizedApp: this.applicationId.replaceAll("-", ""),
        };
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-events-application": ApplicationEvents;
    }
}
