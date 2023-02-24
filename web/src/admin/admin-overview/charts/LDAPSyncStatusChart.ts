import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKChart } from "@goauthentik/elements/charts/Chart";
import "@goauthentik/elements/forms/ConfirmationForm";
import { ChartData, ChartOptions } from "chart.js";

import { t } from "@lingui/macro";

import { customElement } from "lit/decorators.js";

import { SourcesApi, TaskStatusEnum } from "@goauthentik/api";

interface LDAPSyncStats {
    healthy: number;
    failed: number;
    unsynced: number;
}

@customElement("ak-admin-status-chart-ldap-sync")
export class LDAPSyncStatusChart extends AKChart<LDAPSyncStats> {
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

    async apiRequest(): Promise<LDAPSyncStats> {
        const api = new SourcesApi(DEFAULT_CONFIG);
        const sources = await api.sourcesLdapList({});
        const metrics: { [key: string]: number } = {
            healthy: 0,
            failed: 0,
            unsynced: 0,
        };
        await Promise.all(
            sources.results.map(async (element) => {
                // Each source should have 3 successful tasks, so the worst task overwrites
                let sourceKey = "healthy";
                try {
                    const health = await api.sourcesLdapSyncStatusList({
                        slug: element.slug,
                    });

                    health.forEach((task) => {
                        if (task.status !== TaskStatusEnum.Successful) {
                            sourceKey = "failed";
                        }
                        const now = new Date().getTime();
                        const maxDelta = 3600000; // 1 hour
                        if (!health || now - task.taskFinishTimestamp.getTime() > maxDelta) {
                            sourceKey = "unsynced";
                        }
                    });
                } catch {
                    sourceKey = "unsynced";
                }
                metrics[sourceKey] += 1;
            }),
        );
        this.centerText = sources.pagination.count.toString();
        return {
            healthy: metrics.healthy,
            failed: metrics.failed,
            unsynced: sources.pagination.count === 0 ? 1 : metrics.unsynced,
        };
    }

    getChartData(data: LDAPSyncStats): ChartData {
        return {
            labels: [t`Healthy sources`, t`Failed sources`, t`Unsynced sources`],
            datasets: [
                {
                    backgroundColor: ["#3e8635", "#C9190B", "#2b9af3"],
                    spanGaps: true,
                    data: [data.healthy, data.failed, data.unsynced],
                },
            ],
        };
    }
}
