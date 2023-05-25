import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKChart } from "@goauthentik/elements/charts/Chart";
import { ChartData, Tick } from "chart.js";

import { msg, str } from "@lit/localize";
import { customElement, property } from "lit/decorators.js";

import { Coordinate, EventActions, EventsApi } from "@goauthentik/api";

@customElement("ak-charts-admin-model-per-day")
export class AdminModelPerDay extends AKChart<Coordinate[]> {
    @property()
    action: EventActions = EventActions.ModelCreated;

    @property({ attribute: false })
    query?: { [key: string]: unknown } | undefined;

    async apiRequest(): Promise<Coordinate[]> {
        return new EventsApi(DEFAULT_CONFIG).eventsEventsPerMonthList({
            action: this.action,
            query: JSON.stringify(this.query || {}),
        });
    }

    timeTickCallback(tickValue: string | number, index: number, ticks: Tick[]): string {
        const valueStamp = ticks[index];
        const delta = Date.now() - valueStamp.value;
        const ago = Math.round(delta / 1000 / 3600 / 24);
        return msg(str`${ago} days ago`);
    }

    getChartData(data: Coordinate[]): ChartData {
        return {
            datasets: [
                {
                    label: msg("Objects created"),
                    backgroundColor: "rgba(189, 229, 184, .5)",
                    spanGaps: true,
                    data:
                        data.map((cord) => {
                            return {
                                x: cord.xCord || 0,
                                y: cord.yCord || 0,
                            };
                        }) || [],
                },
            ],
        };
    }
}
