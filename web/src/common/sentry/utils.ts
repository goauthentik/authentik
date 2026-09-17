import { SentryIgnoredError } from "#common/sentry/error";

import { RouteInterfaceName } from "#elements/router/utils";

import { CapabilitiesEnum, type ErrorReportingConfig, ResponseError } from "@goauthentik/api";

import { BrowserOptions, ErrorEvent, EventHint, setTag } from "@sentry/browser";

/**
 * Query parameter that turns Sentry off for a single page load.
 */
export const DISABLE_SENTRY_PARAM = "disable-sentry";

/**
 * The configuration needed to determine whether Sentry should report for this page load.
 *
 * @see {@linkcode isSentryEnabled}
 */
export interface SentrySetupOptions {
    /**
     * The deployment's error-reporting configuration.
     *
     * Optional because `Config` types it as required while
     * `ErrorReportingConfigFromJSON` passes a missing value straight through —
     * it is absent whenever the server didn't inject `window.authentik`.
     */
    errorReporting?: ErrorReportingConfig;
    /**
     * Whether the instance reports the `CanDebug` capability.
     */
    debug: boolean;
    /**
     * The current query string, i.e. `window.location.search`.
     */
    search: string;
    /**
     * Whether this is a production build. Defaults to the build-time environment.
     */
    production?: boolean;
}

/**
 * Whether Sentry should report for this page load.
 *
 * The administrator's `errorReporting.enabled` setting decides, in every
 * environment — a deployment that turns error reporting on expects to receive
 * errors. `CanDebug` enables it on its own, which is what activates Spotlight.
 *
 * Development additionally honors `?disable-sentry`, so a noisy local session
 * can opt out for one load without a rebuild.
 *
 * @category Sentry
 */
export function isSentryEnabled({
    errorReporting,
    debug,
    search,
    production = process.env.NODE_ENV === "production",
}: SentrySetupOptions): boolean {
    if (!errorReporting?.enabled && !debug) return false;

    if (production) return true;

    const params = new URLSearchParams(search);

    return !params.has(DISABLE_SENTRY_PARAM);
}

/**
 * A `beforeSend` callback that ignores certain errors.
 *
 * @category Sentry
 */
export function beforeSend(
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
    setTag("authentik.component", `web/${interfaceName}`);
}

/**
 * Default Sentry options for the browser.
 *
 * Free of browser globals at module scope, so the policy this module also
 * exports stays importable outside a document.
 *
 * @category Sentry
 */
export const DEFAULT_SENTRY_BROWSER_OPTIONS = {
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
    release:
        process.env.NODE_ENV === "production"
            ? `authentik@${import.meta.env.AK_VERSION}`
            : undefined,
    beforeSend,
} as const satisfies BrowserOptions;
