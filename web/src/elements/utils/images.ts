import { ResolvedUITheme } from "#common/theme";

import type { LitFC } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import type { ThemedUrls } from "@goauthentik/api";

import { spread } from "@open-wc/lit-helpers";
import { ImgHTMLAttributes } from "react";

import { html, nothing } from "lit";

export const FontAwesomeProtocol = "fa://";

const VALID_ICON_CLASS = /^[a-z0-9-]+$/;

const FA_FAMILY_MAP: Record<string, string> = {
    // Free families
    "solid": "fa-solid",
    "regular": "fa-regular",
    "brands": "fa-brands",
    "fas": "fa-solid",
    "far": "fa-regular",
    "fab": "fa-brands",
    // Pro families (require user-provided FA Pro CSS)
    "light": "fa-light",
    "thin": "fa-thin",
    "duotone": "fa-duotone",
    "fal": "fa-light",
    "fat": "fa-thin",
    "fad": "fa-duotone",
    // Pro sharp families
    "sharp-solid": "fa-sharp fa-solid",
    "sharp-regular": "fa-sharp fa-regular",
    "sharp-light": "fa-sharp fa-light",
    "sharp-thin": "fa-sharp fa-thin",
    "fass": "fa-sharp fa-solid",
    "fasr": "fa-sharp fa-regular",
    "fasl": "fa-sharp fa-light",
    "fast": "fa-sharp fa-thin",
    // Pro sharp-duotone families
    "sharp-duotone-solid": "fa-sharp-duotone fa-solid",
    "sharp-duotone-regular": "fa-sharp-duotone fa-regular",
    "sharp-duotone-light": "fa-sharp-duotone fa-light",
    "sharp-duotone-thin": "fa-sharp-duotone fa-thin",
    "fasds": "fa-sharp-duotone fa-solid",
    "fasdr": "fa-sharp-duotone fa-regular",
    "fasdl": "fa-sharp-duotone fa-light",
    "fasdt": "fa-sharp-duotone fa-thin",
};

/**
 * Parse a fa:// icon string into its family class and icon class.
 *
 * Supported formats:
 *   fa://fa-icon-name              → { family: "fa-solid", iconClass: "fa-icon-name" }
 *   fa://brands/fa-icon-name       → { family: "fa-brands", iconClass: "fa-icon-name" }
 *   fa://regular/fa-icon-name      → { family: "fa-regular", iconClass: "fa-icon-name" }
 *   fa://solid/fa-icon-name        → { family: "fa-solid", iconClass: "fa-icon-name" }
 *   fa://light/fa-icon-name        → { family: "fa-light", iconClass: "fa-icon-name" }
 *   fa://sharp-solid/fa-icon-name  → { family: "fa-sharp fa-solid", iconClass: "fa-icon-name" }
 *
 * Pro families (light, thin, duotone, sharp-*) require FA Pro CSS loaded by the user.
 */
export function parseFontAwesomeIcon(icon: string): { family: string; iconClass: string } {
    const value = icon.slice(FontAwesomeProtocol.length);
    const slashIndex = value.indexOf("/");

    if (slashIndex !== -1) {
        const prefix = value.slice(0, slashIndex).toLowerCase();
        const iconClass = value.slice(slashIndex + 1);
        const family = FA_FAMILY_MAP[prefix] ?? "fa-solid";
        return {
            family,
            iconClass: VALID_ICON_CLASS.test(iconClass) ? iconClass : "fa-question-circle",
        };
    }

    return {
        family: "fa-solid",
        iconClass: VALID_ICON_CLASS.test(value) ? value : "fa-question-circle",
    };
}

export interface ThemedImageProps extends ImgHTMLAttributes<HTMLImageElement> {
    /**
     * The image path (base URL, may contain %(theme)s for display purposes only)
     */
    src: string;
    theme: ResolvedUITheme;
    /**
     * Pre-resolved URLs for each theme variant from backend.
     * When provided, these are used instead of src.
     */
    themedUrls?: ThemedUrls | null;
}

export const ThemedImage: LitFC<ThemedImageProps> = ({
    src,
    className,
    theme,
    themedUrls,
    ...props
}) => {
    if (!src) {
        return nothing;
    }

    // Handle Font Awesome icons
    if (src.startsWith(FontAwesomeProtocol)) {
        const { family, iconClass } = parseFontAwesomeIcon(src);
        const classes = [className, "font-awesome", family, iconClass].filter(Boolean).join(" ");

        return html`<i part="icon font-awesome" role="img" class=${classes} ${spread(props)}></i>`;
    }

    // Use themed URL if available, otherwise use src directly
    const resolvedSrc = (themedUrls as Record<string, string> | null)?.[theme] ?? src;

    return html`<img src=${resolvedSrc} class=${ifPresent(className)} ${spread(props)} />`;
};

export function isDefaultAvatar(path?: string | null): boolean {
    return !!path?.endsWith("user_default.png");
}
