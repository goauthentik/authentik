import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKChart } from "@goauthentik/elements/charts/Chart";
import { ChartData, Tick } from "chart.js";

import { msg, str } from "@lit/localize";
import { customElement, property } from "lit/decorators.js";

import {
    Coordinate,
    EventActions,
    EventVolume,
    EventsApi,
    EventsEventsVolumeListRequest,
} from "@goauthentik/api";

@customElement("ak-charts-admin-model-per-day")
export class AdminModelPerDay extends AKChart<EventVolume[]> {
    @property()
    action: EventActions = EventActions.ModelCreated;

    @property()
    label?: string;

    @property({ attribute: false })
    query?: EventsEventsVolumeListRequest;

    async apiRequest(): Promise<EventVolume[]> {
        return new EventsApi(DEFAULT_CONFIG).eventsEventsVolumeList({
            action: this.action,
            ...this.query,
        });
    }

    getChartData(data: EventVolume[]): ChartData {
        return this.eventVolume(
            data,
            new Map([
                [
                    this.action,
                    {
                        label: this.label || msg("Objects created"),
                        backgroundColor: "rgba(189, 229, 184, .5)",
                        spanGaps: true,
                    },
                ],
            ]),
        );
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-charts-admin-model-per-day": AdminModelPerDay;
    }
}
