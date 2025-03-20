import { VERSION } from "@goauthentik/common/constants";
import { SentryIgnoredError } from "@goauthentik/common/errors";
import { ServerConfig } from "@goauthentik/common/global";
import { me } from "@goauthentik/common/users";
import { browserTracingIntegration, init, setTag, setUser } from "@sentry/browser";

import { CapabilitiesEnum, ResponseError } from "@goauthentik/api";

export const TAG_SENTRY_COMPONENT = "authentik.component";
export const TAG_SENTRY_CAPABILITIES = "authentik.capabilities";

/**
 * Configure Sentry with the given configuration.
 *
 * @param canSendPII Whether the user can send personally identifiable information.
 */
export async function configureSentry(canSendPII?: boolean): Promise<void> {
    if (!ServerConfig.errorReporting.enabled) return;
    const { capabilities, errorReporting } = ServerConfig;

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
        beforeSend: (event, hint) => {
            if (!hint) return event;

            const { originalException } = hint;

            if (originalException instanceof SentryIgnoredError) {
                return null;
            }

            if (originalException instanceof ResponseError) return null;
            if (originalException instanceof DOMException) return null;

            return event;
        },
    });

    setTag(TAG_SENTRY_CAPABILITIES, capabilities.join(","));

    if (window.location.pathname.includes("if/")) {
        setTag(TAG_SENTRY_COMPONENT, `web/${currentInterface()}`);
    }

    if (
        // Retain this predicate order to allow ESBuild to tree-shake the import in production.
        process.env.NODE_ENV === "development" &&
        capabilities.includes(CapabilitiesEnum.CanDebug)
    ) {
        await import("@spotlightjs/spotlight")
            .then((Spotlight) => {
                return Spotlight.init({
                    injectImmediately: true,
                });
            })
            .catch((error) => {
                console.error("Failed to init Spotlight", error);
            });
    }

    if (errorReporting.sendPii && canSendPII) {
        const session = await me().catch(() => null);

        if (session) {
            setUser({ email: session.user.email });
            console.debug("authentik/config: Sentry PII enabled.");
        }
    }

    console.debug("authentik/config: Sentry enabled.");
}

/**
 * Get the current interface from the URL.
 */
export function currentInterface(): string {
    const pathMatches = window.location.pathname.match(/.+if\/(\w+)\//);
    let currentInterface = "unknown";

    if (pathMatches && pathMatches.length >= 2) {
        currentInterface = pathMatches[1];
    }

    return currentInterface.toLowerCase();
}
