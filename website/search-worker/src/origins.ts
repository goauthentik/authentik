/**
 * @file The origins the worker answers: the published sites and every subdomain of
 *   goauthentik.io, Netlify deploy previews, and a local dev server.
 */

const ALLOWED_ORIGINS = [
    /^https:\/\/([a-z0-9-]+\.)*goauthentik\.io$/,
    /^https:\/\/[a-z0-9-]+\.netlify\.app$/,
    /^https?:\/\/localhost(:\d+)?$/,
    /^https?:\/\/127\.0\.0\.1(:\d+)?$/,
];

/**
 * The origin to name in `Access-Control-Allow-Origin`, or `null` when the request's origin is
 * not one the worker answers.
 */
export function allowedOrigin(origin: string): string | null {
    return ALLOWED_ORIGINS.some((pattern) => pattern.test(origin)) ? origin : null;
}
