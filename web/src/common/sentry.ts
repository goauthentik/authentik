import { VERSION } from "@goauthentik/common/constants";
import { RouteInterfaceName, readInterfaceRouteParam } from "@goauthentik/elements/router/utils";
import { BrowserOptions, browserTracingIntegration, init, setTag, setUser } from "@sentry/browser";

import { CapabilitiesEnum, Config, ResponseError, UserSelf } from "@goauthentik/api";

/**
 * A generic error that can be thrown without triggering Sentry's reporting.
 *
 * @category Sentry
 */
export class SentryIgnoredError extends Error {}

/**
 * Attempt initializing Spotlight.
 *
 * @see {@link https://spotlightjs.com/ Spotlight}
 * @category Sentry
 */
export async function tryInitializingSpotlight() {
    return import("@spotlightjs/spotlight").then((Spotlight) =>
        Spotlight.init({ injectImmediately: true }),
    );
}

/**
 * Default Sentry options for the browser.
 *
 * @category Sentry
 */
const DEFAULT_SENTRY_BROWSER_OPTIONS = {
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
    beforeSend: (event, hint) => {
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
} as const satisfies BrowserOptions;

/**
 * Include the given user in Sentry events.
 *
 * @category Sentry
 */
export function setSentryPII(user: UserSelf): void {
    console.debug("authentik/sentry: PII enabled.");

    setUser({ email: user.email });
}

/**
 * Include the given capabilities in Sentry events.
 *
 * @category Sentry
 */
export function setSentryCapabilities(capabilities: CapabilitiesEnum[]): void {
    setTag("authentik.capabilities", capabilities.join(","));
}

/**
 * Include the given route interface in Sentry events.
 *
 * @category Sentry
 */
export function setSentryInterface(interfaceName: RouteInterfaceName) {
    setTag("authentik.component", `web/${interfaceName}}`);
}

/**
 * Attempt to initialize Sentry with the given configuration.
 *
 * @see {@linkcode setSentryPII}
 * @see {@linkcode setSentryCapabilities}
 * @see {@linkcode setSentryInterface}
 * @category Sentry
 */
export function tryInitializeSentry({ errorReporting, capabilities }: Config): void {
    if (!errorReporting.enabled) return;

    init({
        ...DEFAULT_SENTRY_BROWSER_OPTIONS,
        dsn: errorReporting.sentryDsn,
        tracesSampleRate: errorReporting.tracesSampleRate,
        environment: errorReporting.environment,
        enabled: process.env.NODE_ENV !== "development",
    });

    setSentryCapabilities(capabilities);
    setSentryInterface(readInterfaceRouteParam());

    if (
        process.env.NODE_ENV === "development" &&
        capabilities.includes(CapabilitiesEnum.CanDebug)
    ) {
        tryInitializingSpotlight()
            .then(() => {
                console.debug("authentik/sentry: Sentry with Spotlight enabled.");
            })
            .catch((err) => {
                console.warn("authentik/sentry: Failed to load Spotlight", err);
            });
    }
}
