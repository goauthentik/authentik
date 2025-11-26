import { resolveUITheme, rootInterface } from "#common/theme";

import type { AKElement } from "#elements/Base";

import { html, TemplateResult } from "lit";

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
    alt: string = "",
    className: string = "",
): TemplateResult {
    // Handle Font Awesome icons (same logic as ak-app-icon)
    // TODO: I should probably de-duplicate code from there when I have a second
    if (imagePath.startsWith(FontAwesomeProtocol)) {
        const iconClass = imagePath.slice(FontAwesomeProtocol.length);
        return html`<i role="img" aria-label=${alt} class="${className} fas ${iconClass}"></i>`;
    }

    // Handle regular images
    const src = themeImage(imagePath);
    return html`<img src="${src}" alt="${alt}" class="${className}" role="img" />`;
}

export function isDefaultAvatar(path?: string | null): boolean {
    return !!path?.endsWith("user_default.png");
}
