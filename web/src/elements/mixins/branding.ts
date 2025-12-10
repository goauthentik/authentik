import { DefaultBrand } from "#common/ui/config";

import { createMixin } from "#elements/types";

import type { CurrentBrand, FooterLink } from "@goauthentik/api";

import { consume, Context, createContext } from "@lit/context";

/**
 * The Lit context for application branding.
 *
 * @category Context
 * @see {@linkcode BrandingMixin}
 * @see {@linkcode WithBrandConfig}
 */
export const BrandingContext = createContext<CurrentBrand>(
    Symbol.for("authentik-branding-context"),
);

export type BrandingContext = Context<symbol, CurrentBrand>;

/**
 * A mixin that provides the current brand to the element.
 *
 * @see {@linkcode WithBrandConfig}
 */
export interface BrandingMixin {
    /**
     * The current style branding configuration.
     */
    readonly brand: Readonly<CurrentBrand>;

    /**
     * The application title.
     *
     * @see {@linkcode DefaultBrand.brandingTitle}
     */
    readonly brandingTitle: string;

    /**
     * The application logo.
     *
     * @see {@linkcode DefaultBrand.brandingLogo}
     */
    readonly brandingLogo: string;

    /**
     * The application favicon.
     *
     * @see {@linkcode DefaultBrand.brandingFavicon}
     */
    readonly brandingFavicon: string;

    /**
     * Footer links provided by the brand configuration.
     */
    readonly brandingFooterLinks: FooterLink[];
}

/**
 * A mixin that provides the current brand to the element.
 *
 * @category Mixin
 */
export const WithBrandConfig = createMixin<BrandingMixin>(
    ({
        // ---
        SuperClass,
        subscribe = true,
    }) => {
        abstract class BrandingProvider extends SuperClass implements BrandingMixin {
            @consume({
                context: BrandingContext,
                subscribe,
            })
            public brand!: CurrentBrand;

            public get brandingTitle(): string {
                return this.brand.brandingTitle ?? DefaultBrand.brandingTitle;
            }

            public get brandingLogo(): string {
                return this.brand.brandingLogo ?? DefaultBrand.brandingLogo;
            }

            public get brandingFavicon(): string {
                return this.brand.brandingFavicon ?? DefaultBrand.brandingFavicon;
            }

            public get brandingFooterLinks(): FooterLink[] {
                return this.brand.uiFooterLinks ?? DefaultBrand.uiFooterLinks;
            }
        }

        return BrandingProvider;
    },
);
