import { aki } from "#common/api/client";
import { plural } from "#common/ui/locale/plurals";

import { PaginatedResponse } from "#elements/table/Table";

import { StatusGroup, StatusRollupCard } from "#admin/admin-overview/cards/StatusRollupCard";

import { ProvidersApi, SourcesApi, SyncStatus, TaskAggregatedStatusEnum } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { customElement } from "lit/decorators.js";

type SyncState = "synced" | "syncing" | "overdue" | "failed";

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
export class SyncStatusCard extends StatusRollupCard<SyncState> {
    public override icon = "fa fa-sync-alt";
    public override label = msg("Sync status");
    public override tooltip = msg("Integrations synced in the last 12 hours.");

    protected kinds = {
        synced: {
            label: msg("Synced", { id: "admin-overview.sync.legend.synced" }),
            color: "var(--pf-global--success-color--100)",
        },
        syncing: {
            label: msg("Syncing", { id: "admin-overview.sync.legend.syncing" }),
            color: "var(--pf-global--primary-color--100)",
        },
        overdue: {
            label: msg("Overdue", { id: "admin-overview.sync.legend.overdue" }),
            color: "var(--pf-global--warning-color--100)",
        },
        failed: {
            label: msg("Failed", { id: "admin-overview.sync.legend.failed" }),
            color: "var(--pf-global--danger-color--100)",
        },
    };
    protected okKinds: SyncState[] = ["synced", "syncing"];
    protected emptyMessage = msg("Nothing configured to sync.");

    protected summary(total: number) {
        return msg(str`of ${total} synced on schedule`, { id: "admin-overview.sync.summary" });
    }

    async fetchStatus<T>(
        listObjects: () => Promise<PaginatedResponse<T>>,
        fetchSyncStatus: (element: T) => Promise<SyncStatus>,
        label: string,
    ): Promise<StatusGroup<SyncState>> {
        const objects = await listObjects().catch(() => {
            return emptyResponse;
        });

        const counts: Record<SyncState, number> = { synced: 0, syncing: 0, overdue: 0, failed: 0 };

        await Promise.all(
            objects.results.map(async (element) => {
                // Each source should have 3 successful tasks, so the worst task overwrites
                let state: SyncState = "synced";

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
                        state = "failed";
                    } else if (status.isRunning) {
                        state = "syncing";
                    } else if (
                        !status.lastSuccessfulSync ||
                        now - status.lastSuccessfulSync.getTime() > maxDelta
                    ) {
                        state = "overdue";
                    }
                } catch {
                    state = "overdue";
                }

                counts[state] += 1;
            }),
        );

        const total = objects.results.length;

        return {
            label,
            detail: plural(total, {
                one: () => msg("1 integration", { id: "admin-overview.sync.count.one" }),
                other: () =>
                    msg(str`${total} integrations`, { id: "admin-overview.sync.count.other" }),
            }),
            counts,
        };
    }

    async getPrimaryValue(): Promise<StatusGroup<SyncState>[]> {
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
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-admin-status-card-sync": SyncStatusCard;
    }
}
