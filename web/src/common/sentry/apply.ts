/**
 * @file Initializes Sentry as an import side effect.
 *
 * Imported first from each interface entrypoint so reporting is live before the
 * element modules evaluate and custom elements register — errors thrown during
 * that window used to escape, because initialization ran in an element
 * constructor.
 *
 * The enable/disable policy is {@linkcode isSentryEnabled}, which is a pure
 * function so it can be tested without a browser.
 */

import { globalAK } from "#common/global";
import {
    DEFAULT_SENTRY_BROWSER_OPTIONS,
    isSentryEnabled,
    setSentryCapabilities,
    setSentryInterface,
} from "#common/sentry/utils";

import { readInterfaceRouteParam } from "#elements/router/utils";

import { ConsoleLogger } from "#logger/browser";

import { CapabilitiesEnum } from "@goauthentik/api";

import { browserTracingIntegration, init, spotlightBrowserIntegration } from "@sentry/browser";
import { type Integration } from "@sentry/core";

const { errorReporting, capabilities } = globalAK().config;

const debug = capabilities.includes(CapabilitiesEnum.CanDebug);

if (isSentryEnabled({ errorReporting, debug, search: window.location.search })) {
    const logger = ConsoleLogger.prefix("sentry");

    const integrations: Integration[] = [
        browserTracingIntegration({
            // https://docs.sentry.io/platforms/javascript/tracing/instrumentation/automatic-instrumentation/#custom-routing
            instrumentNavigation: false,
            instrumentPageLoad: false,
            traceFetch: false,
        }),
    ];

    if (debug) {
        logger.debug("Enabled Spotlight");
        integrations.push(spotlightBrowserIntegration());
    }

    init({
        ...DEFAULT_SENTRY_BROWSER_OPTIONS,
        integrations,
        tracePropagationTargets: [window.location.origin],
        dsn: errorReporting?.sentryDsn,
        tracesSampleRate: debug ? 1.0 : errorReporting?.tracesSampleRate,
        environment: errorReporting?.environment,
    });

    setSentryCapabilities(capabilities);
    setSentryInterface(readInterfaceRouteParam());
}
