import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKChart, RGBAColor } from "@goauthentik/elements/charts/Chart";
import { ChartData, Tick } from "chart.js";

import { msg, str } from "@lit/localize";
import { customElement } from "lit/decorators.js";

import { AdminApi, LoginMetrics } from "@goauthentik/api";

@customElement("ak-charts-admin-login-authorization")
export class AdminLoginAuthorizeChart extends AKChart<LoginMetrics> {
    async apiRequest(): Promise<LoginMetrics> {
        return new AdminApi(DEFAULT_CONFIG).adminMetricsRetrieve();
    }

    timeTickCallback(tickValue: string | number, index: number, ticks: Tick[]): string {
        const valueStamp = ticks[index];
        const delta = Date.now() - valueStamp.value;
        const ago = Math.round(delta / 1000 / 3600 / 24);
        return msg(str`${ago} day(s) ago`);
    }

    getChartData(data: LoginMetrics): ChartData {
        return {
            datasets: [
                {
                    label: msg("Authorizations"),
                    backgroundColor: new RGBAColor(43, 154, 243, 0.5).toString(),
                    borderColor: new RGBAColor(43, 154, 243, 1).toString(),
                    spanGaps: true,
                    fill: "origin",
                    cubicInterpolationMode: "monotone",
                    tension: 0.4,
                    data: data.authorizations.map((cord) => {
                        return {
                            x: cord.xCord,
                            y: cord.yCord,
                        };
                    }),
                },
                {
                    label: msg("Failed Logins"),
                    backgroundColor: new RGBAColor(201, 24, 11, 0.5).toString(),
                    borderColor: new RGBAColor(201, 24, 11, 1).toString(),
                    spanGaps: true,
                    fill: "origin",
                    cubicInterpolationMode: "monotone",
                    tension: 0.4,
                    data: data.loginsFailed.map((cord) => {
                        return {
                            x: cord.xCord,
                            y: cord.yCord,
                        };
                    }),
                },
                {
                    label: msg("Successful Logins"),
                    backgroundColor: new RGBAColor(62, 134, 53, 0.5).toString(),
                    borderColor: new RGBAColor(62, 134, 53, 1).toString(),
                    spanGaps: true,
                    fill: "origin",
                    cubicInterpolationMode: "monotone",
                    tension: 0.4,
                    data: data.logins.map((cord) => {
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
