import "#elements/forms/ConfirmationForm";

import { AKChart } from "#elements/charts/Chart";
import { actionToColor } from "#elements/charts/EventChart";

import { EventActions } from "@goauthentik/api";

import { ChartData, ChartOptions } from "chart.js";

import { msg } from "@lit/localize";
import { customElement } from "lit/decorators.js";

export interface SummarizedSyncStatus {
    healthy: number;
    failed: number;
    unsynced: number;
    total: number;
    label: string;
}

@customElement("ak-admin-status-chart-sync")
export class SyncStatusChart extends AKChart<SummarizedSyncStatus[]> {
    public override ariaLabel = msg("Synchronization status chart");

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

    async apiRequest(): Promise<SummarizedSyncStatus[]> {
        return [];
    }

    getChartData(data: SummarizedSyncStatus[]): ChartData {
        return {
            labels: [msg("Healthy"), msg("Failed"), msg("Unsynced / N/A")],
            datasets: data.map((d) => {
                return {
                    backgroundColor: [
                        actionToColor(EventActions.Login),
                        actionToColor(EventActions.SuspiciousRequest),
                        actionToColor(EventActions.AuthorizeApplication),
                    ],
                    spanGaps: true,
                    data: [d.healthy, d.failed, d.unsynced],
                    label: d.label,
                };
            }),
        };
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-admin-status-chart-sync": SyncStatusChart;
    }
}
