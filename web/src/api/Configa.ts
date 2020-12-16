import { DefaultClient } from "./Client";
import * as Sentry from "@sentry/browser";
import { Integrations } from "@sentry/tracing";
import { VERSION } from "../constants";
import { SentryIgnoredError } from "../common/errors";

export class Config {
    branding_logo: string;
    branding_title: string;

    error_reporting_enabled: boolean;
    error_reporting_environment: string;
    error_reporting_send_pii: boolean;

    constructor() {
        throw Error();
    }

    static get(): Promise<Config> {
        return DefaultClient.fetch<Config>(["root", "config"]).then((config) => {
            if (config.error_reporting_enabled) {
                Sentry.init({
                    dsn: "https://a579bb09306d4f8b8d8847c052d3a1d3@sentry.beryju.org/8",
                    release: `authentik@${VERSION}`,
                    integrations: [new Integrations.BrowserTracing()],
                    tracesSampleRate: 1.0,
                    environment: config.error_reporting_environment,
                    beforeSend(event: Sentry.Event, hint: Sentry.EventHint) {
                        if (hint.originalException instanceof SentryIgnoredError) {
                            return null;
                        }
                        return event;
                    },
                });
                console.debug("authentik/config: Sentry enabled.");
            }
            return config;
        });
    }
}
