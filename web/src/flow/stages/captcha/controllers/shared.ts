/**
 * @file Shared helpers for matching challenge script URLs to captcha providers.
 */

/**
 * Whether `url` is served by `host` or one of its subdomains.
 *
 * Compared against the registrable host rather than the full origin so that regional and
 * versioned CDN hostnames (`js.hcaptcha.com`, `www.recaptcha.net`) match without having to
 * enumerate them.
 */
export function matchesHost(url: URL, host: string): boolean {
    return url.hostname === host || url.hostname.endsWith(`.${host}`);
}

/**
 * Whether `url` is served by any of `hosts`.
 */
export function matchesAnyHost(url: URL, hosts: readonly string[]): boolean {
    return hosts.some((host) => matchesHost(url, host));
}

/**
 * Whether the URL points at a Cap widget bundle.
 *
 * Cap is self-hosted, so there is no canonical host to match — only the bundle's path
 * shape, which is stable across deployments.
 */
export function isCapWidgetURL(url: URL): boolean {
    return url.pathname.includes("cap-widget") || url.pathname.endsWith("/assets/widget.js");
}
