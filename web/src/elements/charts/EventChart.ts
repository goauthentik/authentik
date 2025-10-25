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

export abstract class EventChart extends AKChart<EventVolume[]> {
    public override ariaLabel = msg("Event volume chart");

    eventVolume(
        data: EventVolume[],
        options?: {
            optsMap?: Map<EventActions, Partial<ChartDataset>>;
            padToDays?: number;
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
        actions.forEach((action) => {
            const actionData: { x: number; y: number }[] = [];
            data.filter((v) => v.action === action).forEach((v) => {
                actionData.push({
                    x: v.time.getTime(),
                    y: v.count,
                });
            });
            // Check if we need to pad the data to reach a certain time window
            const earliestDate = data
                .filter((v) => v.action === action)
                .map((v) => v.time)
                .sort((a, b) => b.getTime() - a.getTime())
                .reverse();
            if (earliestDate.length > 0 && options.padToDays) {
                const earliestPadded = new Date(
                    new Date().getTime() - options.padToDays * (1000 * 3600 * 24),
                );
                const daysDelta = Math.round(
                    (earliestDate[0].getTime() - earliestPadded.getTime()) / (1000 * 3600 * 24),
                );
                if (daysDelta > 0) {
                    actionData.push({
                        x: earliestPadded.getTime(),
                        y: 0,
                    });
                }
            }
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
