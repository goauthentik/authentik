import { DEFAULT_CONFIG } from "#common/api/config";

import { EventChart } from "#elements/charts/EventChart";

import {
    EventActions,
    EventsApi,
    EventsEventsVolumeListRequest,
    EventVolume,
} from "@goauthentik/api";

import { ChartData } from "chart.js";

import { msg } from "@lit/localize";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-charts-admin-model-per-day")
export class AdminModelPerDay extends EventChart {
    @property()
    action: EventActions = EventActions.ModelCreated;

    @property()
    label?: string;

    @property({ attribute: false })
    query?: EventsEventsVolumeListRequest;

    async apiRequest(): Promise<EventVolume[]> {
        return new EventsApi(DEFAULT_CONFIG).eventsEventsVolumeList({
            action: this.action,
            historyDays: 30,
            ...this.query,
        });
    }

    getChartData(data: EventVolume[]): ChartData {
        return this.eventVolume(data, {
            optsMap: new Map([
                [
                    this.action,
                    {
                        label: this.label || msg("Objects created"),
                        spanGaps: true,
                    },
                ],
            ]),
            padToDays: 30,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-charts-admin-model-per-day": AdminModelPerDay;
    }
}
