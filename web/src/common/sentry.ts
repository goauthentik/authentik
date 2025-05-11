import { VERSION } from "@goauthentik/common/constants";
import { globalAK } from "@goauthentik/common/global";
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
import { getTraceData } from "@sentry/core";
import * as Spotlight from "@spotlightjs/spotlight";

import {
    CapabilitiesEnum,
    FetchParams,
    Middleware,
    RequestContext,
    ResponseError,
} from "@goauthentik/api";

/**
 * A generic error that can be thrown without triggering Sentry's reporting.
 */
export class SentryIgnoredError extends Error {}

export const TAG_SENTRY_COMPONENT = "authentik.component";
export const TAG_SENTRY_CAPABILITIES = "authentik.capabilities";

let _sentryConfigured = false;

export function configureSentry(canDoPpi = false) {
    const cfg = globalAK().config;
    const debug = cfg.capabilities.includes(CapabilitiesEnum.CanDebug);
    if (!cfg.errorReporting.enabled && !debug) {
        return cfg;
    }
    init({
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
            browserTracingIntegration({
                // https://docs.sentry.io/platforms/javascript/tracing/instrumentation/automatic-instrumentation/#custom-routing
                instrumentNavigation: false,
                instrumentPageLoad: false,
                traceFetch: false,
            }),
        ],
        tracePropagationTargets: [window.location.origin],
        tracesSampleRate: debug ? 1.0 : cfg.errorReporting.tracesSampleRate,
        environment: cfg.errorReporting.environment,
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
    setTag(TAG_SENTRY_CAPABILITIES, cfg.capabilities.join(","));
    if (window.location.pathname.includes("if/")) {
        setTag(TAG_SENTRY_COMPONENT, `web/${readInterfaceRouteParam()}`);
    }
    if (debug) {
        Spotlight.init({
            injectImmediately: true,
            integrations: [
                Spotlight.sentry({
                    injectIntoSDK: true,
                }),
            ],
        });
        console.debug("authentik/config: Enabled Sentry Spotlight");
    }
    if (cfg.errorReporting.sendPii && canDoPpi) {
        me().then((user) => {
            setUser({ email: user.user.email });
            console.debug("authentik/config: Sentry with PII enabled.");
        });
    } else {
        console.debug("authentik/config: Sentry enabled.");
    }
    _sentryConfigured = true;
}

export class SentryMiddleware implements Middleware {
    pre?(context: RequestContext): Promise<FetchParams | void> {
        if (!_sentryConfigured) {
            return Promise.resolve(context);
        }
        const traceData = getTraceData();
        // @ts-ignore
        context.init.headers["baggage"] = traceData["baggage"];
        // @ts-ignore
        context.init.headers["sentry-trace"] = traceData["sentry-trace"];
        return Promise.resolve(context);
    }
}
