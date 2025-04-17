import { VERSION } from "@goauthentik/common/constants";
import { ServerContext } from "@goauthentik/common/server-context";
import { me } from "@goauthentik/common/users";
import { readInterfaceRouteParam } from "@goauthentik/elements/router/utils";
import {
    ErrorEvent,
    EventHint,
    browserTracingIntegration,
    init,
    setTag,
    setUser,
} from "@sentry/browser";

import { CapabilitiesEnum, ResponseError } from "@goauthentik/api";

/**
 * A generic error that can be thrown without triggering Sentry's reporting.
 */
export class SentryIgnoredError extends Error {}

export const TAG_SENTRY_COMPONENT = "authentik.component";
export const TAG_SENTRY_CAPABILITIES = "authentik.capabilities";

export async function configureSentry(canDoPpi = false): Promise<void> {
    const { errorReporting, capabilities } = ServerContext.config;

    if (!errorReporting.enabled) return;

    init({
        dsn: errorReporting.sentryDsn,
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
            browserTracingIntegration({
                shouldCreateSpanForRequest: (url: string) => {
                    return url.startsWith(window.location.host);
                },
            }),
        ],
        tracesSampleRate: errorReporting.tracesSampleRate,
        environment: errorReporting.environment,
        beforeSend: (
            event: ErrorEvent,
            hint: EventHint,
        ): ErrorEvent | PromiseLike<ErrorEvent | null> | null => {
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

    setTag(TAG_SENTRY_CAPABILITIES, capabilities.join(","));

    if (window.location.pathname.includes("if/")) {
        setTag(TAG_SENTRY_COMPONENT, `web/${readInterfaceRouteParam()}`);
    }

    if (capabilities.includes(CapabilitiesEnum.CanDebug)) {
        const Spotlight = await import("@spotlightjs/spotlight");

        Spotlight.init({ injectImmediately: true });
    }

    if (errorReporting.sendPii && canDoPpi) {
        me().then((user) => {
            setUser({ email: user.user.email });
            console.debug("authentik/config: Sentry with PII enabled.");
        });
    } else {
        console.debug("authentik/config: Sentry enabled.");
    }
}
