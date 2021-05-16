import { t } from "@lingui/macro";
import { customElement } from "lit-element";
import { PoliciesApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../../api/Config";
import "../../../elements/forms/ConfirmationForm";
import { AKChart } from "../../../elements/charts/Chart";
import { ChartData, ChartOptions } from "chart.js";

interface PolicyMetrics {
    count: number;
    cached: number;
    unbound: number;
}

@customElement("ak-admin-status-chart-policy")
export class PolicyStatusChart extends AKChart<PolicyMetrics> {

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

    async apiRequest(): Promise<PolicyMetrics> {
        const api = new PoliciesApi(DEFAULT_CONFIG);
        const cached = (await api.policiesAllCacheInfoRetrieve()).count || 0;
        const count = (await api.policiesAllList({
            pageSize: 1
        })).pagination.count;
        const unbound = (await api.policiesAllList({
            bindingsIsnull: true,
            promptstageIsnull: true,
        })).pagination.count;
        this.centerText = count.toString();
        return {
            count: count - cached - unbound,
            cached: cached,
            unbound: unbound,
        };
    }

    getChartData(data: PolicyMetrics): ChartData {
        return {
            labels: [
                t`Total policies`,
                t`Cached policies`,
                t`Unbound policies`,
            ],
            datasets: [
                {
                    backgroundColor: [
                        "#2b9af3",
                        "#3e8635",
                        "#f0ab00",
                    ],
                    spanGaps: true,
                    data: [
                        data.count,
                        data.cached,
                        data.unbound
                    ],
                },
            ]
        };
    }

}
