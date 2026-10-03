import "#elements/forms/ConfirmationForm";
import { aki } from "#common/api/client";

import { toAdminInterface } from "#elements/router/core/interfaces";

import { AdminStatus, AdminStatusCard } from "#admin/admin-overview/cards/AdminStatusCard";
import { SummarizedSyncStatus } from "#admin/admin-overview/cards/SyncStatusCard";

import { P4Disposition } from "#styles/patternfly/constants";

import { OutpostsApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-admin-status-card-outpost")
export class OutpostStatusCard extends AdminStatusCard<SummarizedSyncStatus[]> {
    public override icon = "pf-icon pf-icon-zone";
    public override label = msg("Outposts");
    public override headerLink = toAdminInterface("outpost/outposts");

    async getPrimaryValue(): Promise<SummarizedSyncStatus[]> {
        const api = aki(OutpostsApi);
        const outposts = await api.outpostsInstancesList({});
        const outpostStats: SummarizedSyncStatus[] = [];

        await Promise.all(
            outposts.results.map(async (element) => {
                const health = await api.outpostsInstancesHealthList({
                    uuid: element.pk || "",
                });

                const singleStats: SummarizedSyncStatus = {
                    unsynced: 0,
                    healthy: 0,
                    failed: 0,
                    total: health.length,
                    label: element.name,
                };

                if (health.length === 0) {
                    singleStats.unsynced += 1;
                }

                health.forEach((h) => {
                    if (h.versionOutdated) {
                        singleStats.failed += 1;
                    } else {
                        singleStats.healthy += 1;
                    }
                });

                outpostStats.push(singleStats);
            }),
        );

        return outpostStats;
    }

    getStatus(value: SummarizedSyncStatus[]): Promise<AdminStatus> {
        const unhealthy = value.filter((v) => v.failed > 0 || v.unsynced > 0).length;

        if (value.length < 1) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-info-circle",
                message: html`${msg("No outposts configured.")}`,
                tone: P4Disposition.Neutral,
            });
        }

        if (unhealthy > 0) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle pf-m-warning",
                message: html`${msg(str`${unhealthy} of ${value.length} outposts need attention.`)}`,
                tone: P4Disposition.Warning,
            });
        }

        return Promise.resolve<AdminStatus>({
            icon: "fa fa-check-circle pf-m-success",
            message: html`${msg("All outposts healthy.")}`,
            tone: P4Disposition.Success,
        });
    }

    renderValue() {
        return html`${this.value?.length}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-admin-status-card-outpost": OutpostStatusCard;
    }
}
