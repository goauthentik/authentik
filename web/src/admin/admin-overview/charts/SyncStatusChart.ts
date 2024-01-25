import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKChart } from "@goauthentik/elements/charts/Chart";
import "@goauthentik/elements/forms/ConfirmationForm";
import { ChartData, ChartOptions } from "chart.js";

import { msg } from "@lit/localize";
import { customElement } from "lit/decorators.js";

import { ProvidersApi, SourcesApi, SystemTaskStatusEnum } from "@goauthentik/api";

export interface SyncStatus {
    healthy: number;
    failed: number;
    unsynced: number;
    total: number;
    label: string;
}

@customElement("ak-admin-status-chart-sync")
export class LDAPSyncStatusChart extends AKChart<SyncStatus[]> {
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

    async ldapStatus(): Promise<SyncStatus> {
        const api = new SourcesApi(DEFAULT_CONFIG);
        const sources = await api.sourcesLdapList({});
        const metrics: { [key: string]: number } = {
            healthy: 0,
            failed: 0,
            unsynced: 0,
        };
        await Promise.all(
            sources.results.map(async (element) => {
                try {
                    const health = await api.sourcesLdapSyncStatusRetrieve({
                        slug: element.slug,
                    });

                    health.tasks.forEach((task) => {
                        if (task.status !== SystemTaskStatusEnum.Successful) {
                            metrics.failed += 1;
                        }
                        const now = new Date().getTime();
                        const maxDelta = 3600000; // 1 hour
                        if (!health || now - task.finishTimestamp.getTime() > maxDelta) {
                            metrics.unsynced += 1;
                        } else {
                            metrics.healthy += 1;
                        }
                    });
                    if (health.tasks.length < 1) {
                        metrics.unsynced += 1;
                    }
                } catch {
                    metrics.unsynced += 1;
                }
            }),
        );
        return {
            healthy: metrics.healthy,
            failed: metrics.failed,
            unsynced: sources.pagination.count === 0 ? 1 : metrics.unsynced,
            total: sources.pagination.count,
            label: msg("LDAP Source"),
        };
    }

    async scimStatus(): Promise<SyncStatus> {
        const api = new ProvidersApi(DEFAULT_CONFIG);
        const providers = await api.providersScimList({});
        const metrics: { [key: string]: number } = {
            healthy: 0,
            failed: 0,
            unsynced: 0,
        };
        await Promise.all(
            providers.results.map(async (element) => {
                // Each source should have 3 successful tasks, so the worst task overwrites
                let sourceKey = "healthy";
                try {
                    const health = await api.providersScimSyncStatusRetrieve({
                        id: element.pk,
                    });
                    health.tasks.forEach((task) => {
                        if (task.status !== SystemTaskStatusEnum.Successful) {
                            sourceKey = "failed";
                        }
                        const now = new Date().getTime();
                        const maxDelta = 3600000; // 1 hour
                        if (!health || now - task.finishTimestamp.getTime() > maxDelta) {
                            sourceKey = "unsynced";
                        }
                    });
                } catch {
                    sourceKey = "unsynced";
                }
                metrics[sourceKey] += 1;
            }),
        );
        return {
            healthy: metrics.healthy,
            failed: metrics.failed,
            unsynced: providers.pagination.count === 0 ? 1 : metrics.unsynced,
            total: providers.pagination.count,
            label: msg("SCIM Provider"),
        };
    }

    async apiRequest(): Promise<SyncStatus[]> {
        const ldapStatus = await this.ldapStatus();
        const scimStatus = await this.scimStatus();
        this.centerText = (ldapStatus.total + scimStatus.total).toString();
        return [ldapStatus, scimStatus];
    }

    getChartData(data: SyncStatus[]): ChartData {
        return {
            labels: [msg("Healthy"), msg("Failed"), msg("Unsynced / N/A")],
            datasets: data.map((d) => {
                return {
                    backgroundColor: ["#3e8635", "#C9190B", "#2b9af3"],
                    spanGaps: true,
                    data: [d.healthy, d.failed, d.unsynced],
                    label: d.label,
                };
            }),
        };
    }
}
