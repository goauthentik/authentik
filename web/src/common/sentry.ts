import { config } from "@goauthentik/common/api/config";
import { VERSION } from "@goauthentik/common/constants";
import { SentryIgnoredError } from "@goauthentik/common/errors";
import { me } from "@goauthentik/common/users";
import * as Sentry from "@sentry/browser";
import { Integrations } from "@sentry/tracing";

import { Config, ResponseError } from "@goauthentik/api";

export const TAG_SENTRY_COMPONENT = "authentik.component";
export const TAG_SENTRY_CAPABILITIES = "authentik.capabilities";

export async function configureSentry(canDoPpi = false): Promise<Config> {
    const cfg = await config();
    if (cfg.errorReporting.enabled) {
        Sentry.init({
            dsn: "https://a579bb09306d4f8b8d8847c052d3a1d3@sentry.beryju.org/8",
            ignoreErrors: [
                /network/gi,
                /fetch/gi,
                /module/gi,
                // Error on edge on ios,
                // https://stackoverflow.com/questions/69261499/what-is-instantsearchsdkjsbridgeclearhighlight
                /instantSearchSDKJSBridgeClearHighlight/gi,
                // Seems to be an issue in Safari and Firefox
                /MutationObserver.observe/gi,
            ],
            release: `authentik@${VERSION()}`,
            tunnel: "/api/v3/sentry/",
            integrations: [
                new Integrations.BrowserTracing({
                    tracingOrigins: [window.location.host, "localhost"],
                }),
            ],
            tracesSampleRate: cfg.errorReporting.tracesSampleRate,
            environment: cfg.errorReporting.environment,
            beforeSend: async (
                event: Sentry.Event,
                hint: Sentry.EventHint | undefined,
            ): Promise<Sentry.Event | null> => {
                if (!hint) {
                    return event;
                }
                if (hint.originalException instanceof SentryIgnoredError) {
                    return null;
                }
                if (
                    hint.originalException instanceof ResponseError ||
                    hint.originalException instanceof DOMException
                ) {
                    return null;
                }
                return event;
            },
        });
        Sentry.setTag(TAG_SENTRY_CAPABILITIES, cfg.capabilities.join(","));
        if (window.location.pathname.includes("if/")) {
            Sentry.setTag(TAG_SENTRY_COMPONENT, `web/${currentInterface()}`);
            Sentry.configureScope((scope) =>
                scope.setTransactionName(`authentik.web.if.${currentInterface()}`),
            );
        }
        if (cfg.errorReporting.sendPii && canDoPpi) {
            me().then((user) => {
                Sentry.setUser({ email: user.user.email });
                console.debug("authentik/config: Sentry with PII enabled.");
            });
        } else {
            console.debug("authentik/config: Sentry enabled.");
        }
    }
    return cfg;
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
