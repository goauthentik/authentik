import { globalAK } from "#common/global";

import { readInterfaceRouteParam } from "#elements/router/utils";

import { CapabilitiesEnum, ResponseError } from "@goauthentik/api";

import {
    browserTracingIntegration,
    ErrorEvent,
    EventHint,
    init,
    setTag,
    spotlightBrowserIntegration,
} from "@sentry/browser";
import { type Integration } from "@sentry/core";

/**
 * A generic error that can be thrown without triggering Sentry's reporting.
 */
export class SentryIgnoredError extends Error {}

export const TAG_SENTRY_COMPONENT = "authentik.component";
export const TAG_SENTRY_CAPABILITIES = "authentik.capabilities";

function beforeSend(
    event: ErrorEvent,
    hint: EventHint,
): ErrorEvent | PromiseLike<ErrorEvent | null> | null {
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
}

export function configureSentry(): void {
    const cfg = globalAK().config;
    const debug = cfg.capabilities.includes(CapabilitiesEnum.CanDebug);

    if (!cfg.errorReporting?.enabled && !debug) {
        return;
    }

    const integrations: Integration[] = [
        browserTracingIntegration({
            // https://docs.sentry.io/platforms/javascript/tracing/instrumentation/automatic-instrumentation/#custom-routing
            instrumentNavigation: false,
            instrumentPageLoad: false,
            traceFetch: false,
        }),
    ];

    if (debug) {
        console.debug("authentik/config: Enabled Sentry Spotlight");
        integrations.push(spotlightBrowserIntegration());
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
        release: `authentik@${import.meta.env.AK_VERSION}`,
        integrations,
        tracePropagationTargets: [window.location.origin],
        tracesSampleRate: debug ? 1.0 : cfg.errorReporting.tracesSampleRate,
        environment: cfg.errorReporting.environment,
        beforeSend,
    });

    setTag(TAG_SENTRY_CAPABILITIES, cfg.capabilities.join(","));

    if (window.location.pathname.includes("if/")) {
        setTag(TAG_SENTRY_COMPONENT, `web/${readInterfaceRouteParam()}`);
    }

    console.debug("authentik/config: Sentry enabled.");
}
