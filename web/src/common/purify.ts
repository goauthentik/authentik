import DOMPurify from "dompurify";
import { trustedTypes } from "trusted-types";

import { render } from "lit";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

/**
 * Trusted types policy that escapes HTML content in place.
 *
 * @see {@linkcode SanitizedTrustPolicy} to strip HTML content.
 *
 * @returns {TrustedHTML} All HTML content, escaped.
 */
export const EscapeTrustPolicy = trustedTypes.createPolicy("authentik-escape", {
    createHTML: (untrustedHTML: string) => {
        return DOMPurify.sanitize(untrustedHTML, {
            RETURN_TRUSTED_TYPE: false,
        });
    },
});

/**
 * Trusted types policy, stripping all HTML content.
 *
 * @returns {TrustedHTML} Text content only, all HTML tags stripped.
 */
export const SanitizedTrustPolicy = trustedTypes.createPolicy("authentik-sanitize", {
    createHTML: (untrustedHTML: string) => {
        return DOMPurify.sanitize(untrustedHTML, {
            RETURN_TRUSTED_TYPE: false,
            ALLOWED_TAGS: ["#text"],
        });
    },
});

/**
 * Trusted types policy, allowing a minimal set of _safe_ HTML tags supplied by
 * a trusted source, such as the brand API.
 */
export const BrandedHTMLPolicy = trustedTypes.createPolicy("authentik-restrict", {
    createHTML: (untrustedHTML: string) => {
        return DOMPurify.sanitize(untrustedHTML, {
            RETURN_TRUSTED_TYPE: false,
            FORBID_TAGS: [
                "script",
                "style",
                "iframe",
                "link",
                "object",
                "embed",
                "applet",
                "meta",
                "base",
                "form",
                "input",
                "textarea",
                "select",
                "button",
            ],
            FORBID_ATTR: [
                "onerror",
                "onclick",
                "onload",
                "onmouseover",
                "onmouseout",
                "onmouseup",
                "onmousedown",
                "onfocus",
                "onblur",
                "onsubmit",
            ],
        });
    },
});

export type AuthentikTrustPolicy =
    | typeof EscapeTrustPolicy
    | typeof SanitizedTrustPolicy
    | typeof BrandedHTMLPolicy;

/**
 * Sanitize an untrusted HTML string using a trusted types policy.
 */
export function sanitizeHTML(trustPolicy: AuthentikTrustPolicy, untrustedHTML: string) {
    return unsafeHTML(trustPolicy.createHTML(untrustedHTML).toString());
}

/**
 * DOMPurify configuration for strict sanitization.
 *
 * This configuration only allows text nodes and disallows all HTML tags.
 */
export const DOM_PURIFY_STRICT = {
    ALLOWED_TAGS: ["#text"],
} as const satisfies DOMPurify.Config;

/**
 * Render untrusted HTML to a string without escaping it.
 *
 * @returns {string} The rendered HTML string.
 */
export function renderStaticHTMLUnsafe(untrustedHTML: unknown): string {
    const container = document.createElement("html");
    render(untrustedHTML, container);

    const result = container.innerHTML;

    return result;
}
