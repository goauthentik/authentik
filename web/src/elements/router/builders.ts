import { globalAK } from "#common/global";

/**
 * Application route helpers.
 *
 * @TODO: This API isn't quite right yet. Revisit after the hash router is replaced.
 */
export const ApplicationRoute = {
    EditURL(slug: string, base = globalAK().api.base) {
        return `${base}if/admin/#/core/applications/${slug}`;
    },
} as const;
