import { customElement, property } from "lit-element";
import { Coordinate, CoreApi } from "../../api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { AKChart } from "./Chart";

@customElement("ak-charts-application-authorize")
export class ApplicationAuthorizeChart extends AKChart<Coordinate[]> {

    @property()
    applicationSlug!: string;

    apiRequest(): Promise<Coordinate[]> {
        return new CoreApi(DEFAULT_CONFIG).coreApplicationsMetrics({ slug: this.applicationSlug });
    }

    getDatasets(data: Coordinate[]): Chart.ChartDataSets[] {
        return [
            {
                label: "Authorizations",
                backgroundColor: "rgba(189, 229, 184, .5)",
                spanGaps: true,
                data: data.map((cord) => {
                    return {
                        x: cord.xCord,
                        y: cord.yCord,
                    };
                }),
            },
        ];
    }

}
