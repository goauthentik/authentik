import { DefaultClient } from "./client";
import * as Sentry from "@sentry/browser";
import { Integrations } from "@sentry/tracing";
import { VERSION } from "../constants";

export class Config {
    branding_logo?: string;
    branding_title?: string;

    error_reporting_enabled?: boolean;
    error_reporting_environment?: string;
    error_reporting_send_pii?: boolean;

    static get(): Promise<Config> {
        return DefaultClient.fetch<Config>(["root", "config"]).then((config) => {
            if (config.error_reporting_enabled) {
                Sentry.init({
                    dsn: "https://33cdbcb23f8b436dbe0ee06847410b67@sentry.beryju.org/3",
                    release: `passbook@${VERSION}`,
                    integrations: [new Integrations.BrowserTracing()],
                    tracesSampleRate: 1.0,
                    environment: config.error_reporting_environment,
                });
                console.debug(`passbook/config: Sentry enabled.`);
            }
            return config;
        });
    }
}
