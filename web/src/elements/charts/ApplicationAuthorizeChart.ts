import { customElement, property } from "lit-element";
import { Coordinate, CoreApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { AKChart } from "./Chart";
import { ChartData } from "chart.js";

@customElement("ak-charts-application-authorize")
export class ApplicationAuthorizeChart extends AKChart<Coordinate[]> {

    @property()
    applicationSlug!: string;

    apiRequest(): Promise<Coordinate[]> {
        return new CoreApi(DEFAULT_CONFIG).coreApplicationsMetricsList({ slug: this.applicationSlug });
    }

    getChartData(data: Coordinate[]): ChartData {
        return {
            datasets: [
                {
                    label: "Authorizations",
                    backgroundColor: "rgba(189, 229, 184, .5)",
                    spanGaps: true,
                    data: data.map((cord) => {
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
