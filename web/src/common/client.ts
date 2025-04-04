/**
 * @file Client-side utilities.
 */
import { TITLE_DEFAULT } from "@goauthentik/common/constants";
import { isAdminRoute } from "@goauthentik/elements/router";

import { msg } from "@lit/localize";

import type { CurrentBrand } from "@goauthentik/api";

type BrandTitleLike = Partial<Pick<CurrentBrand, "brandingTitle">>;

/**
 * Create a title for the page.
 *
 * @param brand - The brand object to append to the title.
 * @param segments - The segments to prepend to the title.
 */
export function formatPageTitle(
    brand: BrandTitleLike | undefined,
    ...segments: Array<string | undefined>
): string;
/**
 * Create a title for the page.
 *
 * @param segments - The segments to prepend to the title.
 */
export function formatPageTitle(...segments: Array<string | undefined>): string;
/**
 * Create a title for the page.
 *
 * @param args - The segments to prepend to the title.
 * @param args - The brand object to append to the title.
 */
export function formatPageTitle(
    ...args: [BrandTitleLike | string | undefined, ...Array<string | undefined>]
): string {
    const segments: string[] = [];

    if (isAdminRoute()) {
        segments.push(msg("Admin"));
    }

    const [arg1, ...rest] = args;

    if (typeof arg1 === "object") {
        const { brandingTitle = TITLE_DEFAULT } = arg1;
        segments.push(brandingTitle);
    } else {
        segments.push(TITLE_DEFAULT);
    }

    for (const segment of rest) {
        if (segment) {
            segments.push(segment);
        }
    }

    return segments.join(" - ");
}
