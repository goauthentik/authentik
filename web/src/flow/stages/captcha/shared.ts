/**
 * @file Shared types and constants for CAPTCHA vendors.
 */

/**
 * The slot a CAPTCHA widget's container is projected through.
 *
 * reCAPTCHA and hCaptcha resolve their internals through `document`, so a container whose
 * `getRootNode()` is a `ShadowRoot` can never finish verifying. The container therefore
 * lives in the flow executor's light DOM — in the document tree — and is forwarded down to
 * the stage through a chain of slots, which projects it into the card without moving it.
 */
export const CAPTCHA_SLOT = "captcha";

/**
 * CAPTCHA vendor identifiers.
 */
export const CaptchaVendor = {
    reCAPTCHA: "recaptcha",
    hCaptcha: "hcaptcha",
    turnstile: "turnstile",
    cap: "cap",
} as const satisfies Record<string, string>;

export type CaptchaVendor = (typeof CaptchaVendor)[keyof typeof CaptchaVendor];

export const CaptchaVendorGlobal: Record<CaptchaVendor, string> = {
    [CaptchaVendor.reCAPTCHA]: "grecaptcha",
    [CaptchaVendor.hCaptcha]: "hcaptcha",
    [CaptchaVendor.turnstile]: "turnstile",
    [CaptchaVendor.cap]: "cap-widget",
};

export type CaptchaVendorGlobal = (typeof CaptchaVendorGlobal)[keyof typeof CaptchaVendorGlobal];

//#region URL matching

/**
 * Whether `url` is served by `host` or one of its subdomains.
 *
 * Compared against the registrable host rather than the full origin so that regional and
 * versioned CDN hostnames (`js.hcaptcha.com`, `www.recaptcha.net`) match without having to
 * enumerate them.
 */
export function matchesHost(url: URL, ...hosts: string[]): boolean {
    return hosts.some((host) => url.hostname === host || url.hostname.endsWith(`.${host}`));
}

export type CaptchaVendorURLPredicate = (url: URL) => boolean;

/**
 * Whether the URL points at a Cap widget bundle.
 *
 * Cap is self-hosted, so there is no canonical host to match — only the bundle's path
 * shape, which is stable across deployments.
 */
export const isCapWidgetURL: CaptchaVendorURLPredicate = (url: URL): boolean => {
    return url.pathname.includes("cap-widget") || url.pathname.endsWith("/assets/widget.js");
};

const CaptchaVendorURLPredicate: Record<CaptchaVendor, CaptchaVendorURLPredicate> = {
    [CaptchaVendor.reCAPTCHA]: (url) =>
        matchesHost(url, "google.com", "recaptcha.net", "gstatic.com") &&
        url.pathname.includes("/recaptcha/"),
    [CaptchaVendor.hCaptcha]: (url) => matchesHost(url, "hcaptcha.com"),
    [CaptchaVendor.turnstile]: (url) => matchesHost(url, "challenges.cloudflare.com"),
    [CaptchaVendor.cap]: isCapWidgetURL,
};

/**
 * Whether `url` is the script URL of `vendor`.
 */
export function matchesVendorURL(vendor: CaptchaVendor, url: URL): boolean {
    return CaptchaVendorURLPredicate[vendor](url);
}

/**
 * The vendor serving `url`, if it is one we recognize.
 */
export function findVendorByURL(url: string | URL | null | undefined): CaptchaVendor | null {
    if (!url) return null;

    if (typeof url === "string" && !URL.canParse(url)) return null;

    const parsed = typeof url === "string" ? new URL(url) : url;

    return Object.values(CaptchaVendor).find((vendor) => matchesVendorURL(vendor, parsed)) ?? null;
}

//#endregion
