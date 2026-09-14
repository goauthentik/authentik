/**
 * @file Whether the initialized Sentry client is reporting.
 *
 * Deliberately a leaf module: it imports the Sentry SDK and nothing else, so
 * router outlets can read the reporting decision without pulling in the app
 * context (`globalAK`, the API client) that Sentry initialization needs.
 */

import { getClient } from "@sentry/browser";
import { type Client } from "@sentry/core";

/**
 * Whether Sentry was initialized and is reporting.
 *
 * The enable/disable policy lives with Sentry initialization, which decides once
 * and leaves the result on the client. Callers read the decision back off the
 * client rather than re-deriving it — a second copy of the policy drifts from
 * the first.
 *
 * Mirrors the SDK's own `_isEnabled()`: `enabled` is optional, and an unset
 * value means enabled. Testing it for truthiness instead would report every
 * client as disabled whenever initialization decides up front and passes no
 * `enabled` at all.
 *
 * @param client The client to inspect. Defaults to the current one.
 */
export function sentryReporting(client: Client | undefined = getClient()): boolean {
    return !!client && client.getOptions().enabled !== false;
}
