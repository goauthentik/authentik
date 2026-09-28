import { aki } from "#common/api/client";

import { PaginatedResponse } from "#elements/table/Table";

import { AdminStatus, AdminStatusCard } from "#admin/admin-overview/cards/AdminStatusCard";

import { ProvidersApi, SourcesApi, SyncStatus, TaskAggregatedStatusEnum } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

export interface SummarizedSyncStatus {
    healthy: number;
    failed: number;
    unsynced: number;
    total: number;
    label: string;
}

const emptyResponse = {
    pagination: {
        next: 0,
        previous: 0,
        count: 0,
        current: 1,
        totalPages: 1,
        startIndex: 1,
        endIndex: 0,
    },
    results: [],
};

@customElement("ak-admin-status-card-sync")
export class SyncStatusCard extends AdminStatusCard<SummarizedSyncStatus[]> {
    public override icon = "fa fa-sync-alt";
    public override label = msg("Sync status");
    public override tooltip = msg("Integrations synced in the last 12 hours.");

    async fetchStatus<T>(
        listObjects: () => Promise<PaginatedResponse<T>>,
        fetchSyncStatus: (element: T) => Promise<SyncStatus>,
        label: string,
    ): Promise<SummarizedSyncStatus> {
        const objects = await listObjects().catch(() => {
            return emptyResponse;
        });

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
                    // 12 hours in milliseconds.
                    const maxDelta = 12 * 60 * 60 * 1000;

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
            label,
        };
    }

    async getPrimaryValue(): Promise<SummarizedSyncStatus[]> {
        return [
            await this.fetchStatus(
                () => {
                    return aki(ProvidersApi).providersScimList();
                },
                (element) => {
                    return aki(ProvidersApi).providersScimSyncStatusRetrieve({
                        id: element.pk,
                    });
                },
                msg("SCIM Provider"),
            ),
            await this.fetchStatus(
                () => {
                    return aki(ProvidersApi).providersGoogleWorkspaceList();
                },
                (element) => {
                    return aki(ProvidersApi).providersGoogleWorkspaceSyncStatusRetrieve({
                        id: element.pk,
                    });
                },
                msg("Google Workspace Provider"),
            ),
            await this.fetchStatus(
                () => {
                    return aki(ProvidersApi).providersMicrosoftEntraList();
                },
                (element) => {
                    return aki(ProvidersApi).providersMicrosoftEntraSyncStatusRetrieve({
                        id: element.pk,
                    });
                },
                msg("Microsoft Entra Provider"),
            ),
            await this.fetchStatus(
                () => {
                    return aki(SourcesApi).sourcesLdapList();
                },
                (element) => {
                    return aki(SourcesApi).sourcesLdapSyncStatusRetrieve({
                        slug: element.slug,
                    });
                },
                msg("LDAP Source"),
            ),
            await this.fetchStatus(
                () => {
                    return aki(SourcesApi).sourcesKerberosList();
                },
                (element) => {
                    return aki(SourcesApi).sourcesKerberosSyncStatusRetrieve({
                        slug: element.slug,
                    });
                },
                msg("Kerberos Source"),
            ),
        ];
    }

    getStatus(value: SummarizedSyncStatus[]): Promise<AdminStatus> {
        const total = value.reduce((sum, v) => sum + v.total, 0);

        // Categories with nothing configured report a placeholder "unsynced" entry;
        // don't count those toward the health signal.
        const unhealthy = value.reduce(
            (sum, v) => sum + v.failed + (v.total > 0 ? v.unsynced : 0),
            0,
        );

        if (total < 1) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-info-circle",
                message: html`${msg("Nothing configured to sync.")}`,
                tone: "neutral",
            });
        }

        if (unhealthy > 0) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle pf-m-warning",
                message: html`${msg(str`${unhealthy} of ${total} syncs need attention.`)}`,
                tone: "warning",
            });
        }

        return Promise.resolve<AdminStatus>({
            icon: "fa fa-check-circle pf-m-success",
            message: html`${msg("Synced.")}`,
            tone: "success",
        });
    }

    renderValue() {
        return html`${this.value?.reduce((sum, v) => sum + v.total, 0) ?? 0}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-admin-status-card-sync": SyncStatusCard;
    }
}
