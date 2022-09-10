import { DEFAULT_CONFIG } from "@goauthentik/web/api/Config";
import { AKChart } from "@goauthentik/web/elements/charts/Chart";
import "@goauthentik/web/elements/forms/ConfirmationForm";
import { ChartData, ChartOptions } from "chart.js";

import { t } from "@lingui/macro";

import { customElement } from "lit/decorators.js";

import { PoliciesApi } from "@goauthentik/api";

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
        const count = (
            await api.policiesAllList({
                pageSize: 1,
            })
        ).pagination.count;
        const unbound = (
            await api.policiesAllList({
                bindingsIsnull: true,
                promptstageIsnull: true,
            })
        ).pagination.count;
        this.centerText = count.toString();
        return {
            // If we have more cache than total policies, only show that
            // otherwise show count without unbound
            count: cached >= count ? cached : count - unbound,
            cached: cached,
            unbound: unbound,
        };
    }

    getChartData(data: PolicyMetrics): ChartData {
        return {
            labels: [t`Total policies`, t`Cached policies`, t`Unbound policies`],
            datasets: [
                {
                    backgroundColor: ["#2b9af3", "#3e8635", "#f0ab00"],
                    spanGaps: true,
                    data: [data.count, data.cached, data.unbound],
                },
            ],
        };
    }
}
