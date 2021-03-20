import { customElement } from "lit-element";
import Chart from "chart.js";
import { CoreApi, UserMetrics } from "authentik-api";
import { AKChart } from "./Chart";
import { DEFAULT_CONFIG } from "../../api/Config";

@customElement("ak-charts-user")
export class UserChart extends AKChart<UserMetrics> {

    apiRequest(): Promise<UserMetrics> {
        return new CoreApi(DEFAULT_CONFIG).coreUsersMetrics({});
    }

    getDatasets(data: UserMetrics): Chart.ChartDataSets[] {
        return [
            {
                label: "Failed Logins",
                backgroundColor: "rgba(201, 25, 11, .5)",
                spanGaps: true,
                data: data.loginsFailedPer1h?.map((cord) => {
                    return {
                        x: cord.xCord,
                        y: cord.yCord,
                    };
                }),
            },
            {
                label: "Successful Logins",
                backgroundColor: "rgba(189, 229, 184, .5)",
                spanGaps: true,
                data: data.loginsPer1h?.map((cord) => {
                    return {
                        x: cord.xCord,
                        y: cord.yCord,
                    };
                }),
            },
            {
                label: "Application authorizations",
                backgroundColor: "rgba(43, 154, 243, .5)",
                spanGaps: true,
                data: data.loginsPer1h?.map((cord) => {
                    return {
                        x: cord.xCord,
                        y: cord.yCord,
                    };
                }),
            },
        ];
    }

}
