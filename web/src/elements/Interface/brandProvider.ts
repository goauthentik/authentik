import { DefaultBrand } from "#common/ui/config";
import { createMixin } from "#elements/types";

import { consume, createContext } from "@lit/context";

import type { CurrentBrand, FooterLink } from "@goauthentik/api";

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

    readonly brandingTitle: string;
    readonly brandingLogo: string;
    readonly brandingFavicon: string;
    readonly brandingFooterLinks: FooterLink[];
}

/**
 * A mixin that provides the current brand to the element.
 *
 * @category Mixin
 *
 * @see {@link https://lit.dev/docs/composition/mixins/#mixins-in-typescript | Lit Mixins}
 */
export const WithBrandConfig = createMixin<BrandingMixin>(
    ({
        /**
         * The superclass constructor to extend.
         */
        SuperClass,
        /**
         * Whether or not to subscribe to the context.
         */
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
