import { toAdminInterface } from "#elements/router/core/interfaces";

/**
 * Application route helpers.
 */
export const ApplicationRoute = {
    EditURL(slug: string) {
        return toAdminInterface(`core/applications/${slug}`);
    },
} as const;
