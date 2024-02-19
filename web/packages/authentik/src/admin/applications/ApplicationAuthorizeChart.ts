import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKChart } from "@goauthentik/elements/charts/Chart";
import { ChartData, Tick } from "chart.js";

import { msg, str } from "@lit/localize";
import { customElement, property } from "lit/decorators.js";

import { Coordinate, CoreApi } from "@goauthentik/api";

@customElement("ak-charts-application-authorize")
export class ApplicationAuthorizeChart extends AKChart<Coordinate[]> {
    @property()
    applicationSlug!: string;

    async apiRequest(): Promise<Coordinate[]> {
        return new CoreApi(DEFAULT_CONFIG).coreApplicationsMetricsList({
            slug: this.applicationSlug,
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
                    label: msg("Authorizations"),
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
