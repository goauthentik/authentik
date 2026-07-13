/**
 * @file Router pattern constants for path-based routing.
 *
 * Raw `URLPattern` pathname-group regex sources used to type path parameters.
 * App-context-free.
 */

/**
 * Slug pattern, matching alphanumeric characters, underscores, and hyphens.
 */
export const SLUG_PATTERN = "[a-zA-Z0-9_\\-]+";

/**
 * Numeric ID pattern, typically used for database IDs.
 */
export const ID_PATTERN = "\\d+";

/**
 * UUID pattern (hex groups).
 *
 * @todo Enforcing this format on the front-end may be too strict; revisit if a
 * non-canonical UUID needs to route.
 */
export const UUID_PATTERN = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}";
