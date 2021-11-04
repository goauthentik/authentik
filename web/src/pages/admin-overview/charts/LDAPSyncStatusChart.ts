import { ChartData, ChartOptions } from "chart.js";

import { t } from "@lingui/macro";

import { customElement } from "lit/decorators.js";

import { SourcesApi, StatusEnum } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../../api/Config";
import { AKChart } from "../../../elements/charts/Chart";
import "../../../elements/forms/ConfirmationForm";

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
        let healthy = 0;
        let failed = 0;
        let unsynced = 0;
        await Promise.all(
            sources.results.map(async (element) => {
                try {
                    const health = await api.sourcesLdapSyncStatusList({
                        slug: element.slug,
                    });
                    health.forEach((task) => {
                        if (task.status !== StatusEnum.Successful) {
                            failed += 1;
                        }
                        const now = new Date().getTime();
                        const maxDelta = 3600000; // 1 hour
                        if (!health || now - task.taskFinishTimestamp.getTime() > maxDelta) {
                            unsynced += 1;
                        } else {
                            healthy += 1;
                        }
                    });
                } catch {
                    unsynced += 1;
                }
            }),
        );
        this.centerText = sources.pagination.count.toString();
        return {
            healthy: sources.pagination.count === 0 ? -1 : healthy,
            failed,
            unsynced,
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
