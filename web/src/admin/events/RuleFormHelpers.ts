import { DEFAULT_CONFIG } from "#common/api/config";

import { DataProvider, DualSelectPair, DualSelectPairSource } from "#elements/ak-dual-select/types";

import { EventsApi, NotificationTransport } from "@goauthentik/api";

export type TransportSelect = [pk: string, name: string];

const transportToSelect = (transport: NotificationTransport): TransportSelect => [
    transport.pk,
    transport.name,
];

export const eventTransportsProvider: DataProvider = async (page = 1, search = "") => {
    const eventTransports = await new EventsApi(DEFAULT_CONFIG).eventsTransportsList({
        ordering: "name",
        pageSize: 20,
        search: search.trim(),
        page,
    });

    return {
        pagination: eventTransports.pagination,
        options: eventTransports.results.map(transportToSelect),
    };
};

export function eventTransportsSelector(
    instanceTransports: string[] | undefined,
): DualSelectPairSource<NotificationTransport> {
    if (!instanceTransports) {
        return (async (transports) =>
            transports.filter(
                ([_0, _1, _2, stage]: DualSelectPair<NotificationTransport>) => stage !== undefined,
            )) satisfies DualSelectPairSource<NotificationTransport>;
    }

    return (async () => {
        const transportsApi = new EventsApi(DEFAULT_CONFIG);
        const transports = await Promise.allSettled(
            instanceTransports.map((instanceId) =>
                transportsApi.eventsTransportsRetrieve({ uuid: instanceId }),
            ),
        );

        return transports
            .filter((s) => s.status === "fulfilled")
            .map((s) => s.value)
            .map(transportToSelect);
    }) satisfies DualSelectPairSource<NotificationTransport>;
}
