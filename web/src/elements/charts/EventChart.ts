import { actionToLabel } from "#common/labels";

import { AKChart } from "#elements/charts/Chart";

import { EventActions, EventVolume } from "@goauthentik/api";

import { ChartData, ChartDataset } from "chart.js";

import { msg } from "@lit/localize";

export function actionToColor(action: EventActions): string {
    switch (action) {
        case EventActions.AuthorizeApplication:
            return "#0060c0";
        case EventActions.ConfigurationError:
            return "#23511e";
        case EventActions.EmailSent:
            return "#009596";
        case EventActions.FlowExecution:
            return "#f4c145";
        case EventActions.ImpersonationEnded:
            return "#a2d9d9";
        case EventActions.ImpersonationStarted:
            return "#a2d9d9";
        case EventActions.InvitationUsed:
            return "#8bc1f7";
        case EventActions.Login:
            return "#4cb140";
        case EventActions.LoginFailed:
            return "#ec7a08";
        case EventActions.Logout:
            return "#f9e0a2";
        case EventActions.ModelCreated:
            return "#8f4700";
        case EventActions.ModelDeleted:
            return "#002f5d";
        case EventActions.ModelUpdated:
            return "#bde2b9";
        case EventActions.PasswordSet:
            return "#003737";
        case EventActions.PolicyException:
            return "#c58c00";
        case EventActions.PolicyExecution:
            return "#f4b678";
        case EventActions.PropertyMappingException:
            return "#519de9";
        case EventActions.SecretRotate:
            return "#38812f";
        case EventActions.SecretView:
            return "#73c5c5";
        case EventActions.SourceLinked:
            return "#f6d173";
        case EventActions.SuspiciousRequest:
            return "#c46100";
        case EventActions.SystemException:
            return "#004b95";
        case EventActions.SystemTaskException:
            return "#7cc674";
        case EventActions.SystemTaskExecution:
            return "#005f60";
        case EventActions.UpdateAvailable:
            return "#f0ab00";
        case EventActions.UserWrite:
            return "#ef9234";
    }

    return "";
}

// The full list of bucket timestamps spanning the last `days`, spaced `stepHours`
// apart and aligned to the backend's own bucket boundaries. The API doesn't expose
// its bucketing directly, so alignment is inferred from an actual data timestamp
// (falling back to epoch-aligned steps when there's no data to anchor to).
function buildBucketGrid(data: EventVolume[], days: number, stepHours: number): number[] {
    const stepMs = stepHours * 60 * 60 * 1000;
    const now = new Date().getTime();
    const windowStart = now - days * 24 * 60 * 60 * 1000;
    const anchor = data.length ? data[0].time.getTime() : Math.ceil(windowStart / stepMs) * stepMs;

    const grid: number[] = [];
    let t = anchor - Math.ceil((anchor - windowStart) / stepMs) * stepMs;

    while (t <= now) {
        if (t >= windowStart) grid.push(t);
        t += stepMs;
    }

    return grid;
}

export abstract class EventChart extends AKChart<EventVolume[]> {
    public override ariaLabel = msg("Event volume chart");

    eventVolume(
        data: EventVolume[],
        options?: {
            optsMap?: Map<EventActions, Partial<ChartDataset>>;
            padToDays?: number;
            stepHours?: number;
        },
    ): ChartData {
        const datasets: ChartData = {
            datasets: [],
        };

        if (!options) {
            options = {};
        }

        if (!options.optsMap) {
            options.optsMap = new Map<EventActions, Partial<ChartDataset>>();
        }

        const actions = new Set(data.map((v) => v.action));

        // Every action's dataset is built against this same fixed grid of bucket
        // timestamps, rather than just the timestamps that happen to have events,
        // so bars stay a uniform width even across stretches with no data.
        const bucketTimes = options.padToDays
            ? buildBucketGrid(data, options.padToDays, options.stepHours ?? 6)
            : null;

        actions.forEach((action) => {
            const countByTime = new Map<number, number>();

            data.filter((v) => v.action === action).forEach((v) => {
                countByTime.set(v.time.getTime(), v.count);
            });

            const actionData: { x: number; y: number }[] = bucketTimes
                ? bucketTimes.map((x) => ({ x, y: countByTime.get(x) ?? 0 }))
                : Array.from(countByTime, ([x, y]) => ({ x, y }));

            datasets.datasets.push({
                data: actionData,
                label: actionToLabel(action),
                backgroundColor: actionToColor(action),
                ...options.optsMap?.get(action),
            });
        });

        return datasets;
    }
}
