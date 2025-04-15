import { Config, ConfigFromJSON, CurrentBrand, CurrentBrandFromJSON } from "@goauthentik/api";

export interface APIConfig {
    /**
     * Absolute base path to the API.
     */
    base: string;
    /**
     * Relative base path to the API.
     */
    relBase: string;
}

export interface FlowConfig {
    /**
     * The current flow ID.
     */
    layout: string;
}

export interface SerializedClientState {
    /**
     * The BCP47 language tag.
     */
    locale?: string;
    /**
     * Current flow state.
     */
    flow?: FlowConfig;
    /**
     * Server configuration.
     */
    config: unknown;
    /**
     * Branding information.
     */
    brand: unknown;
    /**
     * The major and minor components of the current version.
     */
    versionFamily: string;
    /**
     * A subdomain compatible SemVer.
     */
    versionSubdomain: string;
    /**
     * The current build hash.
     */
    build: string;

    /**
     * The API configuration.
     */
    api: APIConfig;
}

type ClientConfigRealm<T> = T & {
    readonly authentik: Readonly<SerializedClientState>;
};

function isClientConfigRealm<T>(namespace: object): namespace is ClientConfigRealm<T> {
    return typeof namespace === "object" && "authentik" in namespace;
}

/**
 * The current locale as defined by the server.
 *
 * @format BCP47
 */
export let ServerLocale = "";

export let FlowConfig: FlowConfig | undefined;

/**
 * The current build hash.
 */
export let BuildHash = "";

/**
 * The major and minor components of the SemVer.
 */
export let VersionFamily = "";

/**
 * A subdomain compatible SemVer.
 */
export let VersionSubdomain = "";

/**
 * The parsed API configuration extracted from the global scope.
 */
export let APIConfig: Readonly<APIConfig>;

/**
 * The parsed server configuration extracted from the global scope.
 */
export let ServerConfig: Readonly<Config>;

/**
 * The parsed brand configuration extracted from the global scope.
 */
export let BrandConfig: Readonly<CurrentBrand>;

if (!isClientConfigRealm(self)) {
    const apiOrigin = new URL(process.env.AK_API_BASE_PATH || window.location.origin);

    APIConfig = {
        base: apiOrigin.toString(),
        relBase: apiOrigin.pathname,
    };

    BrandConfig = CurrentBrandFromJSON({
        ui_footer_links: [],
    });
} else {
    ServerLocale = self.authentik.locale || "";
    FlowConfig = self.authentik.flow;

    BuildHash = self.authentik.build;

    VersionFamily = self.authentik.versionFamily;
    VersionSubdomain = self.authentik.versionSubdomain;

    ServerConfig = ConfigFromJSON(self.authentik.config);
    BrandConfig = CurrentBrandFromJSON(self.authentik.brand);
    APIConfig = self.authentik.api;
}

/**
 * Generate a link to the documentation.
 */
export function docLink(documentationPath: string): string {
    const origin =
        // Default case or beta build which should always point to latest
        BuildHash || !VersionSubdomain
            ? "https://goauthentik.io"
            : `https://${VersionSubdomain}.goauthentik.io`;

    const docsURL = new URL(documentationPath, origin);

    return docsURL.toString();
}
