/**
 * @file An error that opts out of Sentry reporting.
 *
 * Deliberately import-free. This module is pulled in by form and API helpers
 * across all three interfaces, none of which want the Sentry SDK or the
 * generated API client dragged along with the class.
 */

/**
 * A generic error that can be thrown without triggering Sentry's reporting.
 *
 * @see {@linkcode beforeSend} in `sentry/utils.ts`, which drops these events.
 *
 * @category Sentry
 */
export class SentryIgnoredError extends Error {}
