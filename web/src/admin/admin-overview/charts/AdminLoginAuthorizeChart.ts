import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKChart, RGBAColor } from "@goauthentik/elements/charts/Chart";
import { ChartData } from "chart.js";

import { t } from "@lingui/macro";

import { customElement } from "lit/decorators.js";

import { AdminApi, LoginMetrics } from "@goauthentik/api";

@customElement("ak-charts-admin-login-authorization")
export class AdminLoginAuthorizeChart extends AKChart<LoginMetrics> {
    apiRequest(): Promise<LoginMetrics> {
        return new AdminApi(DEFAULT_CONFIG).adminMetricsRetrieve();
    }

    getChartData(data: LoginMetrics): ChartData {
        return {
            datasets: [
                {
                    label: t`Authorizations`,
                    backgroundColor: new RGBAColor(43, 154, 243, 0.5).toString(),
                    borderColor: new RGBAColor(43, 154, 243, 1).toString(),
                    spanGaps: true,
                    fill: "origin",
                    cubicInterpolationMode: "monotone",
                    tension: 0.4,
                    data: data.authorizationsPer1h.map((cord) => {
                        return {
                            x: cord.xCord,
                            y: cord.yCord,
                        };
                    }),
                },
                {
                    label: t`Failed Logins`,
                    backgroundColor: new RGBAColor(201, 24, 11, 0.5).toString(),
                    borderColor: new RGBAColor(201, 24, 11, 1).toString(),
                    spanGaps: true,
                    fill: "origin",
                    cubicInterpolationMode: "monotone",
                    tension: 0.4,
                    data: data.loginsFailedPer1h.map((cord) => {
                        return {
                            x: cord.xCord,
                            y: cord.yCord,
                        };
                    }),
                },
                {
                    label: t`Successful Logins`,
                    backgroundColor: new RGBAColor(62, 134, 53, 0.5).toString(),
                    borderColor: new RGBAColor(62, 134, 53, 1).toString(),
                    spanGaps: true,
                    fill: "origin",
                    cubicInterpolationMode: "monotone",
                    tension: 0.4,
                    data: data.loginsPer1h.map((cord) => {
                        return {
                            x: cord.xCord,
                            y: cord.yCord,
                        };
                    }),
                },
            ],
        };
    }
}
