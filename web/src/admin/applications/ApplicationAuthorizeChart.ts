import { EventChart } from "#elements/charts/EventChart";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { ChartData } from "chart.js";

import { msg } from "@lit/localize";
import { customElement, property } from "lit/decorators.js";

import { EventActions, EventVolume, EventsApi } from "@goauthentik/api";

@customElement("ak-charts-application-authorize")
export class ApplicationAuthorizeChart extends EventChart {
    @property({ attribute: "application-id" })
    applicationId!: string;

    async apiRequest(): Promise<EventVolume[]> {
        return new EventsApi(DEFAULT_CONFIG).eventsEventsVolumeList({
            action: EventActions.AuthorizeApplication,
            contextAuthorizedApp: this.applicationId.replaceAll("-", ""),
        });
    }

    getChartData(data: EventVolume[]): ChartData {
        return this.eventVolume(data, {
            optsMap: new Map([
                [
                    EventActions.AuthorizeApplication,
                    {
                        label: msg("Authorizations"),
                        spanGaps: true,
                    },
                ],
            ]),
            padToDays: 7,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-charts-application-authorize": ApplicationAuthorizeChart;
    }
}
