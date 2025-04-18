/**
 * @file Server context singleton.
 */
import { Config, ConfigFromJSON, CurrentBrand, CurrentBrandFromJSON } from "@goauthentik/api";

function readMetaElement(key: string, fallback: string = ""): string {
    const metaElement = document.querySelector<HTMLMetaElement>(`meta[name="${key}"]`);
    const value = metaElement?.getAttribute("content") || fallback;

    return value;
}

interface ServerContextValue {
    /**
     * Server-injected authentik configuration.
     */
    config: Readonly<Config>;

    /**
     * Brand information used to customize the UI.
     */
    brand: Readonly<CurrentBrand>;

    /**
     * A semantic versioning string representing the current version of authentik.
     */
    versionFamily: string;

    /**
     * A subdomain-compatible version string representing the current version of authentik.
     */
    versionSubdomain: string;

    /**
     * A build hash string representing the current build of authentik.
     */
    build: string;

    /**
     * The base URL of the authentik instance.
     */
    baseURL: string;

    /**
     * The relative base URL of the authentik instance.
     */
    baseURLRelative: string;

    /**
     * The layout of the flow, if any.
     */
    flowLayout: string;

    /**
     * The Sentry trace ID for the current request.
     */
    sentryTrace: string;
}

/**
 * Reads the server context from the DOM.
 */
export function refreshServerContext(): Readonly<ServerContextValue> {
    const configElement = document.getElementById(":ak-config:");

    const config = configElement?.textContent
        ? ConfigFromJSON(JSON.parse(configElement.textContent))
        : ConfigFromJSON({
              capabilities: [],
          });

    const brandElement = document.getElementById(":ak-brand:");

    const brand = brandElement?.textContent
        ? CurrentBrandFromJSON(JSON.parse(brandElement.textContent))
        : CurrentBrandFromJSON({
              ui_footer_links: [],
          });

    const apiBaseURL = new URL(process.env.AK_API_BASE_PATH || window.location.origin);

    const value: ServerContextValue = {
        sentryTrace: readMetaElement("sentry-trace"),
        baseURL: readMetaElement("ak-base-url") || apiBaseURL.toString(),
        baseURLRelative: readMetaElement("ak-base-url-rel"),

        versionFamily: readMetaElement("ak-version-family"),
        versionSubdomain: readMetaElement("ak-version-subdomain"),

        build: readMetaElement("ak-build"),

        flowLayout: readMetaElement("ak-flow-layout"),
        config,
        brand,
    };

    return value;
}

/**
 * Server injected values used to configure application.
 *
 * @singleton
 */
export const ServerContext = refreshServerContext();

export function docLink(path: string): string {
    const { build, versionSubdomain } = ServerContext;

    // Default case or beta build which should always point to latest
    if (build) {
        return new URL(path, "https://goauthentik.io").toString();
    }

    return new URL(path, `https://${versionSubdomain}.goauthentik.io`).toString();
}
