import * as Sentry from "@sentry/browser";
import { Integrations } from "@sentry/tracing";
import { VERSION } from "../constants";
import { SentryIgnoredError } from "../common/errors";
import { me } from "./Users";
import { config } from "./Config";
import { Config } from "@goauthentik/api";

export const TAG_SENTRY_COMPONENT = "authentik.component";
export const TAG_SENTRY_CAPABILITIES = "authentik.capabilities";

export function configureSentry(canDoPpi: boolean = false): Promise<Config> {
    return config().then((config) => {
        if (config.errorReportingEnabled) {
            Sentry.init({
                dsn: "https://a579bb09306d4f8b8d8847c052d3a1d3@sentry.beryju.org/8",
                ignoreErrors: [
                    /network/i,
                ],
                release: `authentik@${VERSION}`,
                tunnel: "/api/v3/sentry/",
                integrations: [
                    new Integrations.BrowserTracing({
                        tracingOrigins: [window.location.host, "localhost"],
                    }),
                ],
                tracesSampleRate: 0.6,
                environment: config.errorReportingEnvironment,
                beforeSend: async (event: Sentry.Event, hint: Sentry.EventHint): Promise<Sentry.Event | null> => {
                    if (hint.originalException instanceof SentryIgnoredError) {
                        return null;
                    }
                    if ((hint.originalException as Error | undefined)?.hasOwnProperty("name")) {
                        if ((hint.originalException as Error | undefined)?.name == 'NetworkError') {
                            return null;
                        }
                    }
                    if (hint.originalException instanceof Response || hint.originalException instanceof DOMException) {
                        return null;
                    }
                    return event;
                },
            });
            Sentry.setTag(TAG_SENTRY_CAPABILITIES, config.capabilities.join(","));
            if (window.location.pathname.includes("if/")) {
                // Get the interface name from URL
                const intf = window.location.pathname.replace(/.+if\/(.+)\//, "$1");
                Sentry.setTag(TAG_SENTRY_COMPONENT, `web/${intf}`);
            }
            if (config.errorReportingSendPii && canDoPpi) {
                me().then(user => {
                    Sentry.setUser({ email: user.user.email });
                    console.debug("authentik/config: Sentry with PII enabled.");
                });
            } else {
                console.debug("authentik/config: Sentry enabled.");
            }
        }
        return config;
    });
}
