import { aki } from "#common/api/client";
import { plural } from "#common/ui/locale/plurals";

import { toAdminInterface } from "#elements/router/core/interfaces";

import { StatusGroup, StatusRollupCard } from "#admin/admin-overview/cards/StatusRollupCard";

import { OutpostsApi, OutpostTypeEnum } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { customElement } from "lit/decorators.js";

type OutpostState = "healthy" | "outdated" | "unreachable";

type OutpostCounts = Record<OutpostState, number>;

const typeLabels: Partial<Record<OutpostTypeEnum, string>> = {
    [OutpostTypeEnum.Proxy]: "Proxy",
    [OutpostTypeEnum.Ldap]: "LDAP",
    [OutpostTypeEnum.Radius]: "RADIUS",
    [OutpostTypeEnum.Rac]: "RAC",
};

@customElement("ak-admin-status-card-outpost")
export class OutpostStatusCard extends StatusRollupCard<OutpostState> {
    public override icon = "pf-icon pf-icon-zone";
    public override label = msg("Outposts");
    public override headerLink = toAdminInterface("outpost/outposts");

    protected kinds = {
        healthy: {
            label: msg("Healthy", { id: "admin-overview.outposts.legend.healthy" }),
            color: "var(--pf-global--success-color--100)",
        },
        outdated: {
            label: msg("Outdated", { id: "admin-overview.outposts.legend.outdated" }),
            color: "var(--pf-global--warning-color--100)",
        },
        unreachable: {
            label: msg("Unreachable", { id: "admin-overview.outposts.legend.unreachable" }),
            color: "var(--pf-global--Color--200)",
        },
    };
    protected okKinds: OutpostState[] = ["healthy"];
    protected emptyMessage = msg("No outposts configured.");

    protected summary(total: number) {
        return plural(total, {
            one: () =>
                msg(str`of ${total} instance healthy`, {
                    id: "admin-overview.outposts.summary.one",
                }),
            other: () =>
                msg(str`of ${total} instances healthy`, {
                    id: "admin-overview.outposts.summary.other",
                }),
        });
    }

    async getPrimaryValue(): Promise<StatusGroup<OutpostState>[]> {
        const api = aki(OutpostsApi);
        const outposts = await api.outpostsInstancesList({});
        const types = new Map<OutpostTypeEnum, { outposts: number; counts: OutpostCounts }>();

        await Promise.all(
            outposts.results.map(async (outpost) => {
                const health = await api.outpostsInstancesHealthList({ uuid: outpost.pk });
                const outdated = health.filter((h) => h.versionOutdated).length;

                const entry = types.get(outpost.type) ?? {
                    outposts: 0,
                    counts: { healthy: 0, outdated: 0, unreachable: 0 },
                };

                entry.outposts += 1;
                entry.counts.healthy += health.length - outdated;
                entry.counts.outdated += outdated;
                // Health is only reported while an instance is connected,
                // so an outpost without any is unreachable.
                entry.counts.unreachable += health.length ? 0 : 1;
                types.set(outpost.type, entry);
            }),
        );

        return Array.from(types, ([type, { outposts, counts }]) => {
            const instances = counts.healthy + counts.outdated + counts.unreachable;

            const o = plural(outposts, {
                one: () => msg("1 outpost", { id: "admin-overview.outposts.count.one" }),
                other: () =>
                    msg(str`${outposts} outposts`, { id: "admin-overview.outposts.count.other" }),
            });

            const i = plural(instances, {
                one: () => msg("1 instance", { id: "admin-overview.outposts.instances.one" }),
                other: () =>
                    msg(str`${instances} instances`, {
                        id: "admin-overview.outposts.instances.other",
                    }),
            });

            return { label: typeLabels[type] ?? type, detail: `${o} · ${i}`, counts };
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-admin-status-card-outpost": OutpostStatusCard;
    }
}
