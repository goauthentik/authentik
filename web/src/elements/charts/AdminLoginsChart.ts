import { customElement } from "lit-element";
import Chart from "chart.js";
import { AdminApi, LoginMetrics } from "authentik-api";
import { AKChart } from "./Chart";
import { DEFAULT_CONFIG } from "../../api/Config";

@customElement("ak-charts-admin-login")
export class AdminLoginsChart extends AKChart<LoginMetrics> {

    apiRequest(): Promise<LoginMetrics> {
        return new AdminApi(DEFAULT_CONFIG).adminMetricsList();
    }

    getDatasets(data: LoginMetrics): Chart.ChartDataSets[] {
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
        ];
    }

}
