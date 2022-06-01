import * as Sentry from "@sentry/browser";
import { Integrations } from "@sentry/tracing";
import { VERSION } from "../constants";
import { SentryIgnoredError } from "../common/errors";
import { me } from "./Users";
import { config } from "./Config";
import { Config } from "@goauthentik/api";

export const TAG_SENTRY_COMPONENT = "authentik.component";
export const TAG_SENTRY_CAPABILITIES = "authentik.capabilities";

export function configureSentry(canDoPpi = false): Promise<Config> {
    return config().then((config) => {
        if (config.errorReporting.enabled) {
            Sentry.init({
                dsn: "https://a579bb09306d4f8b8d8847c052d3a1d3@sentry.beryju.org/8",
                ignoreErrors: [
                    /network/ig,
                    /fetch/ig,
                    // Error on edge on ios,
                    // https://stackoverflow.com/questions/69261499/what-is-instantsearchsdkjsbridgeclearhighlight
                    /instantSearchSDKJSBridgeClearHighlight/ig,
                    // Seems to be an issue in Safari and Firefox
                    /MutationObserver.observe/ig,
                ],
                release: `authentik@${VERSION}`,
                tunnel: "/api/v3/sentry/",
                integrations: [
                    new Integrations.BrowserTracing({
                        tracingOrigins: [window.location.host, "localhost"],
                    }),
                ],
                tracesSampleRate: config.errorReporting.tracesSampleRate,
                environment: config.errorReporting.environment,
                beforeSend: async (event: Sentry.Event, hint: Sentry.EventHint | undefined): Promise<Sentry.Event | null> => {
                    if (!hint) {
                        return event;
                    }
                    if (hint.originalException instanceof SentryIgnoredError) {
                        return null;
                    }
                    if (hint.originalException instanceof Response || hint.originalException instanceof DOMException) {
                        return null;
                    }
                    return event;
                },
            });
            Sentry.setTag(TAG_SENTRY_CAPABILITIES, config.capabilities.join(","));
            if (window.location.pathname.includes("if/")) {
                Sentry.setTag(TAG_SENTRY_COMPONENT, `web/${currentInterface()}`);
                Sentry.configureScope((scope) => scope.setTransactionName(`authentik.web.if.${currentInterface()}`));
            }
            if (config.errorReporting.sendPii && canDoPpi) {
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

// Get the interface name from URL
export function currentInterface(): string {
    const pathMatches = window.location.pathname.match(/.+if\/(\w+)\//);
    let currentInterface = "unknown";
    if (pathMatches && pathMatches.length >= 2) {
        currentInterface = pathMatches[1];
    }
    return currentInterface;
}
