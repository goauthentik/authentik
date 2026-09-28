import { aki } from "#common/api/client";

import { ChartCardStat, ChartCardWithStats } from "#elements/cards/ChartCardWithStats";

import { EventActions, EventsApi, EventVolume } from "@goauthentik/api";

import { ChartData, ChartDataset } from "chart.js";

import { msg } from "@lit/localize";
import { customElement } from "lit/decorators.js";

const issueActions: EventActions[] = [
    EventActions.SystemException,
    EventActions.SystemTaskException,
    EventActions.PolicyException,
    EventActions.PropertyMappingException,
];

@customElement("ak-charts-admin-login-authorization")
export class AdminLoginAuthorizeChart extends ChartCardWithStats {
    public override label = msg("Logins and authorizations over the last week (per 8 hours)");

    async apiRequest(): Promise<EventVolume[]> {
        return aki(EventsApi).eventsEventsVolumeList({
            actions: [
                EventActions.AuthorizeApplication,
                EventActions.Login,
                EventActions.LoginFailed,
                ...issueActions
            ],
        });
    }

    getStats(data: EventVolume[]): ChartCardStat[] {
        const totals = new Map<EventActions, number>();
        data.forEach((v) => totals.set(v.action, (totals.get(v.action) ?? 0) + v.count));
        const issueTotal = data
            .map((v) => (issueActions.includes(v.action) ? (v.count ?? 0) : 0))
            .reduce(
                (accumulator, currentValue) => accumulator + currentValue,
                0,
            );
        return [
            { label: msg("Successful logins"), value: `${totals.get(EventActions.Login) ?? 0}` },
            {
                label: msg("Failed logins"),
                value: `${totals.get(EventActions.LoginFailed) ?? 0}`,
            },
            {
                label: msg("Authorizations"),
                value: `${totals.get(EventActions.AuthorizeApplication) ?? 0}`,
            },
            {
                label: msg("Issues"),
                value: `${issueTotal}`,
            },
        ];
    }

    getChartDatasets(data: EventVolume[]): ChartData {
        data = data.filter((v) => !issueActions.includes(v.action));

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
            optsMap,
            padToDays: 7,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-charts-admin-login-authorization": AdminLoginAuthorizeChart;
    }
}
