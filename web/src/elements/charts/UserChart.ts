import { customElement, property } from "lit-element";
import { CoreApi, UserMetrics } from "authentik-api";
import { AKChart } from "./Chart";
import { DEFAULT_CONFIG } from "../../api/Config";
import { ChartData } from "chart.js";

@customElement("ak-charts-user")
export class UserChart extends AKChart<UserMetrics> {

    @property({type: Number})
    userId?: number;

    apiRequest(): Promise<UserMetrics> {
        return new CoreApi(DEFAULT_CONFIG).coreUsersMetricsRetrieve({
            id: this.userId || 0,
        });
    }

    getChartData(data: UserMetrics): ChartData {
        return {
            datasets: [
                {
                    label: "Failed Logins",
                    backgroundColor: "rgba(201, 25, 11, .5)",
                    spanGaps: true,
                    data: data.loginsFailedPer1h?.map((cord) => {
                        return {
                            x: cord.xCord || 0,
                            y: cord.yCord || 0,
                        };
                    }) || [],
                },
                {
                    label: "Successful Logins",
                    backgroundColor: "rgba(189, 229, 184, .5)",
                    spanGaps: true,
                    data: data.loginsPer1h?.map((cord) => {
                        return {
                            x: cord.xCord || 0,
                            y: cord.yCord || 0,
                        };
                    }) || [],
                },
                {
                    label: "Application authorizations",
                    backgroundColor: "rgba(43, 154, 243, .5)",
                    spanGaps: true,
                    data: data.authorizationsPer1h?.map((cord) => {
                        return {
                            x: cord.xCord || 0,
                            y: cord.yCord || 0,
                        };
                    }) || [],
                },
            ]
        };
    }

}
