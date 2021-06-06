import * as Sentry from "@sentry/browser";
import { Integrations } from "@sentry/tracing";
import { VERSION } from "../constants";
import { SentryIgnoredError } from "../common/errors";
import { me } from "./Users";
import { config } from "./Config";
import { Config } from "authentik-api";

export const TAG_SENTRY_COMPONENT = "authentik.component";

export function configureSentry(canDoPpi: boolean = false, tags: { [key: string]: string; } = {}): Promise<Config> {
    return config().then((config) => {
        if (config.errorReportingEnabled) {
            Sentry.init({
                dsn: "https://a579bb09306d4f8b8d8847c052d3a1d3@sentry.beryju.org/8",
                release: `authentik@${VERSION}`,
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
                    if (hint.originalException instanceof Error) {
                        if (hint.originalException.name == 'NetworkError') {
                            return null;
                        }
                    }
                    if (hint.originalException instanceof Response) {
                        const response = hint.originalException as Response;
                        // We only care about server errors
                        if (response.status < 500) {
                            return null;
                        }
                        const body = await response.json();
                        event.message = `${response.status} ${response.url}: ${JSON.stringify(body)}`
                    }
                    if (event.exception) {
                        me().then(user => {
                            Sentry.showReportDialog({
                                eventId: event.event_id,
                                user: {
                                    email: user.user.email,
                                    name: user.user.name,
                                }
                            });
                        });
                    }
                    return event;
                },
            });
            Sentry.setTags(tags);
            if (window.location.pathname.includes("if/")) {
                // Get the interface name from URL
                const intf = window.location.pathname.replace(/.+if\/(.+)\//, "$1");
                Sentry.setTag(TAG_SENTRY_COMPONENT, `web/${intf}`);
            }
            console.debug("authentik/config: Sentry enabled.");
            if (config.errorReportingSendPii && canDoPpi) {
                me().then(user => {
                    Sentry.setUser({ email: user.user.email });
                    console.debug("authentik/config: Sentry with PII enabled.");
                });
            }
        }
        return config;
    });
}
