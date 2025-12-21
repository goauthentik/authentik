import { DEFAULT_CONFIG } from "#common/api/config";

import { EventChart } from "#elements/charts/EventChart";

import { EventActions, EventsApi, EventVolume } from "@goauthentik/api";

import { ChartData, ChartDataset } from "chart.js";

import { msg } from "@lit/localize";
import { customElement } from "lit/decorators.js";

@customElement("ak-charts-admin-login-authorization")
export class AdminLoginAuthorizeChart extends EventChart {
    async apiRequest(): Promise<EventVolume[]> {
        return new EventsApi(DEFAULT_CONFIG).eventsEventsVolumeList({
            actions: [
                EventActions.AuthorizeApplication,
                EventActions.Login,
                EventActions.LoginFailed,
            ],
        });
    }

    getChartData(data: EventVolume[]): ChartData {
        const optsMap = new Map<EventActions, Partial<ChartDataset>>();
        optsMap.set(EventActions.AuthorizeApplication, {
            label: msg("Authorizations"),
            spanGaps: true,
            fill: "origin",
            cubicInterpolationMode: "monotone",
            tension: 0.4,
        });
        optsMap.set(EventActions.Login, {
            label: msg("Successful Logins"),
            spanGaps: true,
            fill: "origin",
            cubicInterpolationMode: "monotone",
            tension: 0.4,
        });
        optsMap.set(EventActions.LoginFailed, {
            label: msg("Failed Logins"),
            spanGaps: true,
            fill: "origin",
            cubicInterpolationMode: "monotone",
            tension: 0.4,
        });
        return this.eventVolume(data, {
            optsMap: optsMap,
            padToDays: 7,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-charts-admin-login-authorization": AdminLoginAuthorizeChart;
    }
}
