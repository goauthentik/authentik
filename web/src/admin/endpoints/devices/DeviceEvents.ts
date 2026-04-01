import "#components/ak-event-info";

import { SimpleEventTable } from "#admin/events/SimpleEventTable";

import { EventsEventsListRequest } from "@goauthentik/api";

import { customElement, property } from "lit/decorators.js";

@customElement("ak-events-device")
export class DeviceEvents extends SimpleEventTable {
    @property({ attribute: "device-id" })
    deviceId!: string;

    async apiParameters(): Promise<Partial<EventsEventsListRequest>> {
        return {
            contextDevice: this.deviceId.replaceAll("-", ""),
        };
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-events-device": DeviceEvents;
    }
}
