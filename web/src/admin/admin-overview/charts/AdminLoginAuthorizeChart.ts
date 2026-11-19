import { aki } from "#common/api/client";

import { ChartCardStat, ChartCardWithStats } from "#elements/cards/ChartCardWithStats";

import { EventActions, EventsApi, EventVolume } from "@goauthentik/api";

import { ChartData, ChartDataset } from "chart.js";

import { msg, str } from "@lit/localize";
import { customElement } from "lit/decorators.js";

const issueActions: EventActions[] = [
    EventActions.SystemException,
    EventActions.SystemTaskException,
    EventActions.PolicyException,
    EventActions.PropertyMappingException,
];

const WEEK_MS = 7 * 24 * 60 * 60 * 1000;

function sumInWindow(data: EventVolume[], actions: EventActions[], from: Date, to: Date): number {
    return data
        .filter((v) => actions.includes(v.action) && v.time >= from && v.time < to)
        .reduce((sum, v) => sum + v.count, 0);
}

// Week-over-week total plus a formatted delta, e.g. "+24% vs previous week".
function weekOverWeek(
    data: EventVolume[],
    actions: EventActions[],
    direction: "up-good" | "up-bad",
): Pick<ChartCardStat, "value" | "delta" | "tone"> {
    const now = new Date();
    const thisWeekStart = new Date(now.getTime() - WEEK_MS);
    const lastWeekStart = new Date(now.getTime() - 2 * WEEK_MS);

    const current = sumInWindow(data, actions, thisWeekStart, now);
    const previous = sumInWindow(data, actions, lastWeekStart, thisWeekStart);
    const diff = current - previous;

    const delta =
        previous === 0
            ? diff === 0
                ? msg("No change vs previous week")
                : msg(str`${diff > 0 ? "+" : ""}${diff} vs previous week`)
            : msg(
                  str`${diff > 0 ? "+" : ""}${Math.round((diff / previous) * 100)}% vs previous week`,
              );

    const tone =
        diff === 0
            ? undefined
            : (direction === "up-good" ? diff > 0 : diff < 0)
              ? "success"
              : "danger";

    return { value: `${current}`, delta, tone };
}

@customElement("ak-charts-admin-login-authorization")
export class AdminLoginAuthorizeChart extends ChartCardWithStats {
    public override label = msg("Logins and authorizations over the last week (per 8 hours)");

    async apiRequest(): Promise<EventVolume[]> {
        return aki(EventsApi).eventsEventsVolumeList({
            actions: [
                EventActions.AuthorizeApplication,
                EventActions.Login,
                EventActions.LoginFailed,
                ...issueActions,
            ],
            // Two weeks, so stats can show a delta against the previous week.
            historyDays: 14,
        });
    }

    getStats(data: EventVolume[]): ChartCardStat[] {
        return [
            {
                label: msg("Successful logins"),
                ...weekOverWeek(data, [EventActions.Login], "up-good"),
            },
            {
                label: msg("Failed logins"),
                ...weekOverWeek(data, [EventActions.LoginFailed], "up-bad"),
            },
            {
                label: msg("Authorizations"),
                ...weekOverWeek(data, [EventActions.AuthorizeApplication], "up-good"),
            },
            {
                label: msg("Issues"),
                ...weekOverWeek(data, issueActions, "up-bad"),
            },
        ];
    }

    getChartDatasets(data: EventVolume[]): ChartData {
        const weekAgo = new Date(Date.now() - WEEK_MS);

        data = data.filter((v) => !issueActions.includes(v.action) && v.time >= weekAgo);

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
