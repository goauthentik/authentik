import {
    CSRFMiddleware,
    DevRepeatedRequestsMiddleware,
    EventMiddleware,
    LocaleMiddleware,
    LoggingMiddleware,
} from "#common/api/middleware";
import { globalAK } from "#common/global";
import { SentryMiddleware } from "#common/sentry/middleware";

import { CapabilitiesEnum, Configuration } from "@goauthentik/api";

type APIConstructor<T> = new (config: Configuration) => T;

let configuration: Configuration | null = null;

const endpoints = new Map<APIConstructor<unknown>, unknown>();

function apiConfiguration(): Configuration {
    if (!configuration) {
        const { locale, api, brand, config } = globalAK();
        configuration = new Configuration({
            basePath: `${api.base}api/v3`,
            middleware: [
                new CSRFMiddleware(),
                new EventMiddleware(),
                new LoggingMiddleware(brand),
                new SentryMiddleware(),
                new LocaleMiddleware(locale),
                ...(config.capabilities.includes(CapabilitiesEnum.CanDebug)
                    ? [new DevRepeatedRequestsMiddleware()]
                    : []),
            ],
        });
        Object.freeze(configuration);
    }
    return configuration;
}

export function aki<T>(APIClass: APIConstructor<T>): T {
    let endpoint = endpoints.get(APIClass) as T | undefined;
    if (!endpoint) {
        endpoint = new APIClass(apiConfiguration());
        endpoints.set(APIClass, endpoint);
    }
    return endpoint;
}
