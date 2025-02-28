import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";
import { DualSelectPair } from "@goauthentik/elements/ak-dual-select/types";

import { EventsApi, NotificationTransport } from "@goauthentik/api";

const transportToSelect = (transport: NotificationTransport) => [transport.pk, transport.name];

export async function eventTransportsProvider(page = 1, search = "") {
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
}

export function eventTransportsSelector(instanceTransports: string[] | undefined) {
    if (!instanceTransports) {
        return async (transports: DualSelectPair<NotificationTransport>[]) =>
            transports.filter(
                ([_0, _1, _2, stage]: DualSelectPair<NotificationTransport>) => stage !== undefined,
            );
    }

    return async () => {
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
    };
}
