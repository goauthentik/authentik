import { resolveUITheme, rootInterface } from "#common/theme";

import type { AKElement } from "#elements/Base";
import type { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { html, nothing } from "lit";

export const FontAwesomeProtocol = "fa://";

export function themeImage(rawPath: string) {
    const enabledTheme = rootInterface<AKElement>()?.activeTheme || resolveUITheme();

    return rawPath.replaceAll("%(theme)s", enabledTheme);
}

/**
 * Renders an image that can be a regular URL, Font Awesome icon (fa://), or themed image
 *
 * @param imagePath - URL, fa:// icon, or path with %(theme)s placeholder
 * @param alt - Alt text for the image
 * @param className - CSS classes to apply
 * @returns TemplateResult with either <img> or <i> element
 */
export function renderImage(
    imagePath: string,
    alt?: string,
    className?: string,
): SlottedTemplateResult {
    if (!imagePath) {
        return nothing;
    }

    // Handle Font Awesome icons (same logic as ak-app-icon)
    if (imagePath.startsWith(FontAwesomeProtocol)) {
        return html`<i
            part="icon font-awesome"
            role="img"
            aria-label=${ifPresent(alt)}
            class="${className} fas ${imagePath.slice(FontAwesomeProtocol.length)}"
        ></i>`;
    }

    const src = themeImage(imagePath);

    return html`<img src=${src} alt=${ifPresent(alt)} class=${ifPresent(className)} />`;
}

export function isDefaultAvatar(path?: string | null): boolean {
    return !!path?.endsWith("user_default.png");
}
