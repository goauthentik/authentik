import { ResolvedUITheme } from "#common/theme";

import type { LitFC } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { spread } from "@open-wc/lit-helpers";
import { ImgHTMLAttributes } from "react";

import { html, nothing } from "lit";

export const FontAwesomeProtocol = "fa://";

export function themeImage(rawPath: string, theme: ResolvedUITheme) {
    return rawPath.replaceAll("%(theme)s", theme);
}

export interface ThemedImageProps extends ImgHTMLAttributes<HTMLImageElement> {
    /**
     * The image path, which can be:
     * - A regular URL
     * - A Font Awesome icon (fa://icon-name)
     * - A themed image path with %(theme)s placeholder
     */
    src: string;
    theme: ResolvedUITheme;
}

export const ThemedImage: LitFC<ThemedImageProps> = ({ src, className, theme, ...props }) => {
    if (!src) {
        return nothing;
    }

    // Handle Font Awesome icons (same logic as ak-app-icon)
    if (src.startsWith(FontAwesomeProtocol)) {
        const classes = [className, "font-awesome", "fas", src.slice(FontAwesomeProtocol.length)]
            .filter(Boolean)
            .join(" ");

        return html`<i part="icon font-awesome" role="img" class=${classes} ${spread(props)}></i>`;
    }

    const themedSrc = themeImage(src, theme);

    return html`<img src=${themedSrc} class=${ifPresent(className)} ${spread(props)} />`;
};

export function isDefaultAvatar(path?: string | null): boolean {
    return !!path?.endsWith("user_default.png");
}
