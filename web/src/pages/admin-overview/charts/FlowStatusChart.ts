import { ChartData, ChartOptions } from "chart.js";

import { t } from "@lingui/macro";

import { customElement } from "lit/decorators.js";

import { FlowsApi } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../../api/Config";
import { AKChart } from "../../../elements/charts/Chart";
import "../../../elements/forms/ConfirmationForm";

interface FlowMetrics {
    count: number;
    cached: number;
}

@customElement("ak-admin-status-chart-flow")
export class PolicyStatusChart extends AKChart<FlowMetrics> {
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
