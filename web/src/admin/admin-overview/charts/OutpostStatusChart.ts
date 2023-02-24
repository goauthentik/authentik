import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKChart } from "@goauthentik/elements/charts/Chart";
import "@goauthentik/elements/forms/ConfirmationForm";
import { ChartData, ChartOptions } from "chart.js";

import { t } from "@lingui/macro";

import { customElement } from "lit/decorators.js";

import { OutpostsApi } from "@goauthentik/api";

interface OutpostStats {
    healthy: number;
    outdated: number;
    unhealthy: number;
}

@customElement("ak-admin-status-chart-outpost")
export class OutpostStatusChart extends AKChart<OutpostStats> {
    getChartType(): string {
        return "doughnut";
    }

    getOptions(): ChartOptions {
        return {
            plugins: {
                legend: {
                    display: false,
                },
            },
            maintainAspectRatio: false,
        };
    }

    async apiRequest(): Promise<OutpostStats> {
        const api = new OutpostsApi(DEFAULT_CONFIG);
        const outposts = await api.outpostsInstancesList({});
        let healthy = 0;
        let outdated = 0;
        let unhealthy = 0;
        await Promise.all(
            outposts.results.map(async (element) => {
                const health = await api.outpostsInstancesHealthList({
                    uuid: element.pk || "",
                });
                if (health.length === 0) {
                    unhealthy += 1;
                }
                health.forEach((h) => {
                    if (h.versionOutdated) {
                        outdated += 1;
                    } else {
                        healthy += 1;
                    }
                });
            }),
        );
        this.centerText = outposts.pagination.count.toString();
        return {
            healthy: healthy,
            outdated: outdated,
            unhealthy: outposts.pagination.count === 0 ? 1 : unhealthy,
        };
    }

    getChartData(data: OutpostStats): ChartData {
        return {
            labels: [t`Healthy outposts`, t`Outdated outposts`, t`Unhealthy outposts`],
            datasets: [
                {
                    backgroundColor: ["#3e8635", "#f0ab00", "#C9190B"],
                    spanGaps: true,
                    data: [data.healthy, data.outdated, data.unhealthy],
                },
            ],
        };
    }
}
