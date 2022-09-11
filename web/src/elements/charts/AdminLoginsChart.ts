import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKChart } from "@goauthentik/elements/charts/Chart";
import { ChartData } from "chart.js";

import { t } from "@lingui/macro";

import { customElement } from "lit/decorators.js";

import { AdminApi, LoginMetrics } from "@goauthentik/api";

@customElement("ak-charts-admin-login")
export class AdminLoginsChart extends AKChart<LoginMetrics> {
    apiRequest(): Promise<LoginMetrics> {
        return new AdminApi(DEFAULT_CONFIG).adminMetricsRetrieve();
    }

    getChartData(data: LoginMetrics): ChartData {
        return {
            datasets: [
                {
                    label: t`Failed Logins`,
                    backgroundColor: "rgba(201, 25, 11, .5)",
                    spanGaps: true,
                    data:
                        data.loginsFailedPer1h?.map((cord) => {
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
                        data.loginsPer1h?.map((cord) => {
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
