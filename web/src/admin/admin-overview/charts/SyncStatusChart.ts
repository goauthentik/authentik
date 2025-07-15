import "#elements/forms/ConfirmationForm";

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKChart } from "#elements/charts/Chart";
import { actionToColor } from "#elements/charts/EventChart";
import { PaginatedResponse } from "#elements/table/Table";

import {
    EventActions,
    ProvidersApi,
    SourcesApi,
    SyncStatus,
    TaskAggregatedStatusEnum,
} from "@goauthentik/api";

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

    async fetchStatus<T>(
        listObjects: () => Promise<PaginatedResponse<T>>,
        fetchSyncStatus: (element: T) => Promise<SyncStatus>,
        label: string,
    ): Promise<SummarizedSyncStatus> {
        const objects = await listObjects();
        const metrics: { [key: string]: number } = {
            healthy: 0,
            failed: 0,
            unsynced: 0,
        };
        await Promise.all(
            objects.results.map(async (element) => {
                // Each source should have 3 successful tasks, so the worst task overwrites
                let objectKey = "healthy";
                try {
                    const status = await fetchSyncStatus(element);

                    const now = new Date().getTime();
                    const maxDelta = 3600000; // 1 hour

                    if (
                        status.lastSyncStatus === TaskAggregatedStatusEnum.Error ||
                        status.lastSyncStatus === TaskAggregatedStatusEnum.Rejected ||
                        status.lastSyncStatus === TaskAggregatedStatusEnum.Warning
                    ) {
                        objectKey = "failed";
                    } else if (
                        !status.lastSuccessfulSync ||
                        now - status.lastSuccessfulSync.getTime() > maxDelta
                    ) {
                        objectKey = "unsynced";
                    }
                } catch {
                    objectKey = "unsynced";
                }
                metrics[objectKey] += 1;
            }),
        );
        return {
            healthy: metrics.healthy,
            failed: metrics.failed,
            unsynced: objects.pagination.count === 0 ? 1 : metrics.unsynced,
            total: objects.pagination.count,
            label: label,
        };
    }

    async apiRequest(): Promise<SummarizedSyncStatus[]> {
        const statuses = [
            await this.fetchStatus(
                () => {
                    return new ProvidersApi(DEFAULT_CONFIG).providersScimList();
                },
                (element) => {
                    return new ProvidersApi(DEFAULT_CONFIG).providersScimSyncStatusRetrieve({
                        id: element.pk,
                    });
                },
                msg("SCIM Provider"),
            ),
            await this.fetchStatus(
                () => {
                    return new ProvidersApi(DEFAULT_CONFIG).providersGoogleWorkspaceList();
                },
                (element) => {
                    return new ProvidersApi(
                        DEFAULT_CONFIG,
                    ).providersGoogleWorkspaceSyncStatusRetrieve({
                        id: element.pk,
                    });
                },
                msg("Google Workspace Provider"),
            ),
            await this.fetchStatus(
                () => {
                    return new ProvidersApi(DEFAULT_CONFIG).providersMicrosoftEntraList();
                },
                (element) => {
                    return new ProvidersApi(
                        DEFAULT_CONFIG,
                    ).providersMicrosoftEntraSyncStatusRetrieve({
                        id: element.pk,
                    });
                },
                msg("Microsoft Entra Provider"),
            ),
            await this.fetchStatus(
                () => {
                    return new SourcesApi(DEFAULT_CONFIG).sourcesLdapList();
                },
                (element) => {
                    return new SourcesApi(DEFAULT_CONFIG).sourcesLdapSyncStatusRetrieve({
                        slug: element.slug,
                    });
                },
                msg("LDAP Source"),
            ),
            await this.fetchStatus(
                () => {
                    return new SourcesApi(DEFAULT_CONFIG).sourcesKerberosList();
                },
                (element) => {
                    return new SourcesApi(DEFAULT_CONFIG).sourcesKerberosSyncStatusRetrieve({
                        slug: element.slug,
                    });
                },
                msg("Kerberos Source"),
            ),
        ];
        this.centerText = statuses.reduce((total, el) => (total += el.total), 0).toString();
        return statuses;
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
