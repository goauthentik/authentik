import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKChart } from "@goauthentik/elements/charts/Chart";
import { ChartData, Tick } from "chart.js";

import { t } from "@lingui/macro";

import { customElement, property } from "lit/decorators.js";

import { CoreApi, UserMetrics } from "@goauthentik/api";

@customElement("ak-charts-user")
export class UserChart extends AKChart<UserMetrics> {
    @property({ type: Number })
    userId?: number;

    async apiRequest(): Promise<UserMetrics> {
        return new CoreApi(DEFAULT_CONFIG).coreUsersMetricsRetrieve({
            id: this.userId || 0,
        });
    }

    timeTickCallback(tickValue: string | number, index: number, ticks: Tick[]): string {
        const valueStamp = ticks[index];
        const delta = Date.now() - valueStamp.value;
        const ago = Math.round(delta / 1000 / 3600 / 24);
        return t`${ago} days ago`;
    }

    getChartData(data: UserMetrics): ChartData {
        return {
            datasets: [
                {
                    label: t`Failed Logins`,
                    backgroundColor: "rgba(201, 25, 11, .5)",
                    spanGaps: true,
                    data:
                        data.loginsFailed?.map((cord) => {
                            return {
                                x: cord.xCord || 0,
                                y: cord.yCord || 0,
                            };
                        }) || [],
                },
                {
                    label: t`Successful Logins`,
                    backgroundColor: "rgba(189, 229, 184, .5)",
                    spanGaps: true,
                    data:
                        data.logins?.map((cord) => {
                            return {
                                x: cord.xCord || 0,
                                y: cord.yCord || 0,
                            };
                        }) || [],
                },
                {
                    label: t`Application authorizations`,
                    backgroundColor: "rgba(43, 154, 243, .5)",
                    spanGaps: true,
                    data:
                        data.authorizations?.map((cord) => {
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
