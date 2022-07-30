import { DEFAULT_CONFIG } from "@goauthentik/web/api/Config";
import { ChartData } from "chart.js";

import { t } from "@lingui/macro";

import { customElement, property } from "lit/decorators.js";

import { Coordinate, CoreApi } from "@goauthentik/api";

import { AKChart } from "./Chart";

@customElement("ak-charts-application-authorize")
export class ApplicationAuthorizeChart extends AKChart<Coordinate[]> {
    @property()
    applicationSlug!: string;

    apiRequest(): Promise<Coordinate[]> {
        return new CoreApi(DEFAULT_CONFIG).coreApplicationsMetricsList({
            slug: this.applicationSlug,
        });
    }

    getChartData(data: Coordinate[]): ChartData {
        return {
            datasets: [
                {
                    label: t`Authorizations`,
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
