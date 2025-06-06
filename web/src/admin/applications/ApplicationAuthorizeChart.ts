import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKChart } from "@goauthentik/elements/charts/Chart";
import { ChartData } from "chart.js";

import { msg } from "@lit/localize";
import { customElement, property } from "lit/decorators.js";

import { EventActions, EventVolume, EventsApi } from "@goauthentik/api";

@customElement("ak-charts-application-authorize")
export class ApplicationAuthorizeChart extends AKChart<EventVolume[]> {
    @property({ attribute: "application-id" })
    applicationId!: string;

    async apiRequest(): Promise<EventVolume[]> {
        return new EventsApi(DEFAULT_CONFIG).eventsEventsVolumeList({
            action: EventActions.AuthorizeApplication,
            contextAuthorizedApp: this.applicationId.replaceAll("-", ""),
        });
    }

    getChartData(data: EventVolume[]): ChartData {
        return this.eventVolume(
            data,
            new Map([
                [
                    EventActions.AuthorizeApplication,
                    {
                        label: msg("Authorizations"),
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
        "ak-charts-application-authorize": ApplicationAuthorizeChart;
    }
}
