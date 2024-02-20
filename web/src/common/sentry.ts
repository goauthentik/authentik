import { config } from "@goauthentik/common/api/config";
import { VERSION } from "@goauthentik/common/constants";
import { SentryIgnoredError } from "@goauthentik/common/errors";
import { me } from "@goauthentik/common/users";
import * as Sentry from "@sentry/browser";

import { CapabilitiesEnum, Config, ResponseError } from "@goauthentik/api";

export const TAG_SENTRY_COMPONENT = "authentik.component";
export const TAG_SENTRY_CAPABILITIES = "authentik.capabilities";

export async function configureSentry(canDoPpi = false): Promise<Config> {
    const cfg = await config();
    if (cfg.errorReporting.enabled) {
        Sentry.init({
            dsn: cfg.errorReporting.sentryDsn,
            ignoreErrors: [
                /network/gi,
                /fetch/gi,
                /module/gi,
                // Error on edge on ios,
                // https://stackoverflow.com/questions/69261499/what-is-instantsearchsdkjsbridgeclearhighlight
                /instantSearchSDKJSBridgeClearHighlight/gi,
                // Seems to be an issue in Safari and Firefox
                /MutationObserver.observe/gi,
                /NS_ERROR_FAILURE/gi,
            ],
            release: `authentik@${VERSION}`,
            integrations: [
                Sentry.browserTracingIntegration({
                    shouldCreateSpanForRequest: (url: string) => {
                        return url.startsWith(window.location.host);
                    },
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
        }
        if (cfg.capabilities.includes(CapabilitiesEnum.CanDebug)) {
            const Spotlight = await import("@spotlightjs/spotlight");

            Spotlight.init({ injectImmediately: true });
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
    return currentInterface.toLowerCase();
}
