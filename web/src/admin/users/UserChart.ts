import { DEFAULT_CONFIG } from "#common/api/config";

import { EventChart } from "#elements/charts/EventChart";

import { EventActions, EventsApi, EventVolume } from "@goauthentik/api";

import { ChartData } from "chart.js";

import { msg } from "@lit/localize";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-charts-user")
export class UserChart extends EventChart {
    @property()
    username?: string;

    async apiRequest(): Promise<EventVolume[]> {
        return new EventsApi(DEFAULT_CONFIG).eventsEventsVolumeList({
            actions: [
                EventActions.Login,
                EventActions.LoginFailed,
                EventActions.AuthorizeApplication,
            ],
            username: this.username,
        });
    }

    getChartData(data: EventVolume[]): ChartData {
        return this.eventVolume(data, {
            optsMap: new Map([
                [
                    EventActions.LoginFailed,
                    {
                        label: msg("Failed Logins"),
                        spanGaps: true,
                    },
                ],
                [
                    EventActions.Login,
                    {
                        label: msg("Successful Logins"),
                        spanGaps: true,
                    },
                ],
                [
                    EventActions.AuthorizeApplication,
                    {
                        label: msg("Application authorizations"),
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
        "ak-charts-user": UserChart;
    }
}
