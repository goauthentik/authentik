/**
 * @file Utilities for managing document metadata, titles, etc.
 */

import { isNamedEntity, NamedEntity } from "#common/api/entities";

import { isAdminRoute } from "#elements/router/utils";
import { SlottedTemplateResult } from "#elements/types";

import type { ThemedUrls } from "@goauthentik/api";

import { msg } from "@lit/localize";

export interface PageHeaderInit {
    header?: string | null;
    description?: SlottedTemplateResult;
    icon?: string | null;
    iconThemedUrls?: ThemedUrls | null;
    iconImage?: boolean;
}

export class PageDetailsUpdate extends Event {
    static readonly eventName = "ak-page-details-update";
    header: PageHeaderInit;

    constructor(header: PageHeaderInit) {
        super(PageDetailsUpdate.eventName, { bubbles: true, composed: true });
        this.header = header;
    }
}

export function setPageDetails(header: PageHeaderInit) {
    window.dispatchEvent(new PageDetailsUpdate(header));
}

export type DocumentTitleSegment = string | null | undefined | NamedEntity;

/**
 * Formats the document title by prepending the provided segments to the branding title, if present.
 *
 * @param brandingTitle The custom branding title e.g. "authentik", "Acme, Inc."
 * @param segments Additional segments to prepend to the document title.
 */
export function formatDocumentTitle(
    brandingTitle: string,
    ...segments: DocumentTitleSegment[]
): string {
    return [
        ...segments.map((segment) => {
            if (typeof segment === "string") {
                return segment.trim();
            }

            if (isNamedEntity(segment)) {
                return segment.verboseName;
            }

            return null;
        }),
        brandingTitle,
    ]
        .filter((segment): segment is string => !!segment)
        .join(" - ");
}

/**
 * Sets the document title using the provided branding title and additional segments.
 *
 * @param brandingTitle The custom branding title e.g. "authentik", "Acme, Inc."
 * @param segments Additional segments to prepend to the document title.
 * @see {@linkcode formatDocumentTitle} for the underlying formatting logic.
 */
export function setTitle(brandingTitle: string, ...segments: DocumentTitleSegment[]): void {
    const formattedBrandingTitle = isAdminRoute()
        ? `${msg("Admin")} - ${brandingTitle}`
        : brandingTitle;

    const title = formatDocumentTitle(formattedBrandingTitle, ...segments);

    if (document.title !== title) {
        document.title = title;
    }
}

declare global {
    interface WindowEventMap {
        [PageDetailsUpdate.eventName]: PageDetailsUpdate;
    }
}
