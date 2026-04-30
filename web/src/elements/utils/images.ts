import { ResolvedUITheme } from "#common/theme";

import type { LitFC } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import type { ThemedUrls } from "@goauthentik/api";

import { spread } from "@open-wc/lit-helpers";
import { ImgHTMLAttributes } from "react";

import { html, nothing, TemplateResult } from "lit";

export const FontAwesomeProtocol = "fa://";
export const FA_FAMILY_MAP: Record<string, string[]> = {
    "brands": ["fa-brands"],
    "fab": ["fa-brands"],
    "fa-brands": ["fa-brands"],
    "duotone": ["fa-duotone"],
    "fad": ["fa-duotone"],
    "fa-duotone": ["fa-duotone"],
    "light": ["fa-light"],
    "fal": ["fa-light"],
    "fa-light": ["fa-light"],
    "regular": ["fa-regular"],
    "far": ["fa-regular"],
    "fa-regular": ["fa-regular"],
    "solid": ["fa-solid"],
    "fas": ["fa-solid"],
    "fa-solid": ["fa-solid"],
    "thin": ["fa-thin"],
    "fat": ["fa-thin"],
    "fa-thin": ["fa-thin"],
    "sharp-solid": ["fa-sharp", "fa-solid"],
    "fass": ["fa-sharp", "fa-solid"],
    "fa-sharp-solid": ["fa-sharp", "fa-solid"],
    "sharp-regular": ["fa-sharp", "fa-regular"],
    "fasr": ["fa-sharp", "fa-regular"],
    "fa-sharp-regular": ["fa-sharp", "fa-regular"],
    "sharp-light": ["fa-sharp", "fa-light"],
    "fasl": ["fa-sharp", "fa-light"],
    "fa-sharp-light": ["fa-sharp", "fa-light"],
    "sharp-thin": ["fa-sharp", "fa-thin"],
    "fast": ["fa-sharp", "fa-thin"],
    "fa-sharp-thin": ["fa-sharp", "fa-thin"],
    "sharp-duotone-solid": ["fa-sharp-duotone", "fa-solid"],
    "fasds": ["fa-sharp-duotone", "fa-solid"],
    "fa-sharp-duotone-solid": ["fa-sharp-duotone", "fa-solid"],
    "sharp-duotone-regular": ["fa-sharp-duotone", "fa-regular"],
    "fasdr": ["fa-sharp-duotone", "fa-regular"],
    "fa-sharp-duotone-regular": ["fa-sharp-duotone", "fa-regular"],
    "sharp-duotone-light": ["fa-sharp-duotone", "fa-light"],
    "fasdl": ["fa-sharp-duotone", "fa-light"],
    "fa-sharp-duotone-light": ["fa-sharp-duotone", "fa-light"],
    "sharp-duotone-thin": ["fa-sharp-duotone", "fa-thin"],
    "fasdt": ["fa-sharp-duotone", "fa-thin"],
    "fa-sharp-duotone-thin": ["fa-sharp-duotone", "fa-thin"],
};
const FontAwesomeStyleClasses = new Set([
    "fa",
    "fab",
    "fad",
    "fal",
    "far",
    "fas",
    "fat",
    "fa-brands",
    "fa-duotone",
    "fa-light",
    "fa-regular",
    "fa-sharp",
    "fa-sharp-duotone",
    "fa-solid",
    "fa-thin",
]);

export function getFontAwesomeClasses(src: string, className?: string): string {
    const rawValue = src.slice(FontAwesomeProtocol.length).trim();
    const [familyKey, iconFromFamily] = rawValue.split("/", 2);
    const familyClasses = FA_FAMILY_MAP[familyKey] ?? [];
    const rawClasses = (familyClasses.length ? iconFromFamily : rawValue)
        .trim()
        .split(/\s+/)
        .filter(Boolean);
    const iconClasses = rawClasses
        .filter((token) => !FontAwesomeStyleClasses.has(token))
        .map((token) => (token.startsWith("fa-") ? token : `fa-${token}`));
    const styleClasses = rawClasses.filter((token) => FontAwesomeStyleClasses.has(token));

    return [
        className,
        "font-awesome",
        ...(familyClasses.length
            ? familyClasses
            : styleClasses.length
              ? styleClasses
              : ["fa-solid"]),
        ...iconClasses,
    ]
        .filter(Boolean)
        .join(" ");
}

export interface VariantUrls {
    fallback?: string | null;
    [key: string]: string | null | undefined;
}

export function resolveVariantUrl(
    variantUrls: VariantUrls | undefined | null,
    theme: ResolvedUITheme | undefined,
): string | undefined | null {
    if (!variantUrls) {
        return undefined;
    }

    if (theme && variantUrls[theme]) {
        return variantUrls[theme];
    }

    if (variantUrls.fallback) {
        return variantUrls.fallback;
    }

    return Object.values(variantUrls).find((url) => !!url);
}

export function resolveThemedUrl(
    src: string | undefined | null,
    themedUrls: ThemedUrls | undefined | null,
    theme: ResolvedUITheme | undefined,
): string | undefined | null {
    const variantUrls = themedUrls ? { ...themedUrls } : {};
    if (src !== undefined && src !== null) {
        variantUrls.fallback = src;
    }
    return resolveVariantUrl(variantUrls, theme);
}

/**
 * The default background image for flows, used when no specific background is set.
 *
 * @todo This feels fragile, especially with theme variables and asset management.
 */
export const DefaultFlowBackground = "/static/dist/assets/images/flow_background.jpg";

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
    part?: string;
    role?: string;
}

export interface RenderIconOptions {
    alt?: string;
    ariaHidden?: boolean;
    ariaLabel?: string;
    className?: string;
    fallback?: TemplateResult | typeof nothing;
    part?: string;
}

export interface RenderDynamicIconOptions extends RenderIconOptions {
    urls: VariantUrls | undefined | null;
    theme: ResolvedUITheme | undefined;
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
        const classes = getFontAwesomeClasses(src, className);

        return html`<i part="icon font-awesome" role="img" class=${classes} ${spread(props)}></i>`;
    }

    // Use themed URL if available, otherwise use src directly
    const resolvedSrc = resolveThemedUrl(src, themedUrls, theme);
    if (!resolvedSrc) {
        return nothing;
    }

    return html`<img src=${resolvedSrc} class=${ifPresent(className)} ${spread(props)} />`;
};

export function renderIcon(
    src: string | undefined | null,
    themedUrls: ThemedUrls | undefined | null,
    theme: ResolvedUITheme | undefined,
    {
        alt = "",
        ariaHidden = false,
        ariaLabel,
        className,
        fallback = nothing,
        part,
    }: RenderIconOptions = {},
): TemplateResult | typeof nothing {
    const resolvedSrc = resolveThemedUrl(src, themedUrls, theme);
    if (!resolvedSrc) {
        return fallback;
    }

    return html`${ThemedImage({
        "src": resolvedSrc,
        alt,
        "aria-hidden": ariaHidden,
        "aria-label": ariaLabel,
        className,
        part,
        "role": ariaHidden ? undefined : "img",
        "theme": theme ?? "light",
    })}`;
}

export function renderDynamicIcon({
    urls,
    theme,
    ...options
}: RenderDynamicIconOptions): TemplateResult | typeof nothing {
    const resolvedSrc = resolveVariantUrl(urls, theme);
    return renderIcon(resolvedSrc, null, theme, options);
}

export function isDefaultAvatar(path?: string | null): boolean {
    return !!path?.endsWith("user_default.png");
}
