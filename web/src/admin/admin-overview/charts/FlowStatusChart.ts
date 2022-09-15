import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKChart } from "@goauthentik/elements/charts/Chart";
import "@goauthentik/elements/forms/ConfirmationForm";
import { ChartData, ChartOptions } from "chart.js";

import { t } from "@lingui/macro";

import { customElement } from "lit/decorators.js";

import { FlowsApi } from "@goauthentik/api";

interface FlowMetrics {
    count: number;
    cached: number;
}

@customElement("ak-admin-status-chart-flow")
export class FlowStatusChart extends AKChart<FlowMetrics> {
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

    async apiRequest(): Promise<FlowMetrics> {
        const api = new FlowsApi(DEFAULT_CONFIG);
        const cached = (await api.flowsInstancesCacheInfoRetrieve()).count || 0;
        const count = (
            await api.flowsInstancesList({
                pageSize: 1,
            })
        ).pagination.count;
        this.centerText = count.toString();
        return {
            count: count - cached,
            cached: cached,
        };
    }

    getChartData(data: FlowMetrics): ChartData {
        return {
            labels: [t`Total flows`, t`Cached flows`],
            datasets: [
                {
                    backgroundColor: ["#2b9af3", "#3e8635"],
                    spanGaps: true,
                    data: [data.count, data.cached],
                },
            ],
        };
    }
}
