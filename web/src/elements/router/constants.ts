/**
 * @file Router constants.
 */

/**
 * Route separator, used to separate the path from the mock query string.
 */
export const ROUTE_SEPARATOR = "?";

/**
 * Slug pattern, matching alphanumeric characters, underscores, and hyphens.
 */
export const SLUG_PATTERN = "[a-zA-Z0-9_\\-]+";

/**
 * Numeric ID pattern, typically used for database IDs.
 */
export const ID_PATTERN = "\\d+";

/**
 * UUID v4 pattern
 *
 * @todo Enforcing this format on the front-end may be a bit too strict.
 * We may want to allow other UUID formats, or move this to a validation step.
 */
export const UUID_PATTERN = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}";
