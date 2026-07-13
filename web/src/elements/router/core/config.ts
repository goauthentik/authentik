/**
 * @file Router configuration injected by each entrypoint at boot.
 *
 * The router core never reads globals. Each entrypoint calls {@linkcode initRouter}
 * once at boot with the deployment base path (read from `window.authentik.api.relBase`
 * **at the entrypoint**) and the interface name. The core only ever receives values.
 */

export interface RouterConfig {
    /**
     * Deployment base path, trailing-slashed. Examples: `/`, `/auth/`.
     */
    base: string;

    /**
     * Interface prefix segment. Examples: `admin`, `user`.
     */
    interfaceName: string;
}

const DEFAULT_CONFIG: RouterConfig = { base: "/", interfaceName: "unknown" };

let currentConfig: RouterConfig = { ...DEFAULT_CONFIG };

/**
 * Configure the router core. Called once by each entrypoint at boot.
 */
export function initRouter(config: RouterConfig): void {
    currentConfig = { ...config };
}

/**
 * Read the current router configuration.
 *
 * @returns A shallow copy — mutations of the returned object do not affect the
 * stored config.
 */
export function getRouterConfig(): RouterConfig {
    return { ...currentConfig };
}

/**
 * Reset the configuration to its defaults.
 *
 * @remarks Test-only. Not for production call sites.
 */
export function resetRouterConfig(): void {
    currentConfig = { ...DEFAULT_CONFIG };
}
